package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"

	"crowdsense/backend/repository"

	"github.com/gorilla/mux"
	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
)

func connectDB() (*sql.DB, error) {
	// Docker環境では環境変数を直接使用するため、.envファイルの読み込みは不要
	_ = godotenv.Load() // エラーを無視

	host := os.Getenv("POSTGRES_HOST")
	port := os.Getenv("POSTGRES_PORT")
	user := os.Getenv("POSTGRES_USER")
	password := os.Getenv("POSTGRES_PASSWORD")
	dbname := os.Getenv("POSTGRES_DB")
	goenv := os.Getenv("GO_ENV")

	if host == "" {
		host = "localhost"
	}
	if port == "" {
		port = "5432"
	}

	var psqlInfo string
	if goenv == "development" {
		psqlInfo = fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
			host, port, user, password, dbname)
	} else {
		psqlInfo = fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s",
			host, port, user, password, dbname)
	}

	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		return nil, err
	}

	err = db.Ping()
	if err != nil {
		return nil, err
	}

	return db, nil
}

func getCloudDataByDateHandler(cloudDataRepo repository.CloudDataRepository) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		vars := mux.Vars(r)
		placeIDStr := vars["placeID"]
		targetDate := vars["targetDate"]

		fmt.Printf("Request received - PlaceID: %s, TargetDate: %s\n", placeIDStr, targetDate)

		placeID, err := strconv.Atoi(placeIDStr)
		if err != nil {
			fmt.Printf("Error parsing placeID: %v\n", err)
			http.Error(w, "Invalid place ID", http.StatusBadRequest)
			return
		}

		cloudData, err := cloudDataRepo.GetCloudDataByDate(placeID, targetDate)
		if err != nil {
			fmt.Printf("Error getting cloud data: %v\n", err)
			http.Error(w, fmt.Sprintf("Failed to get cloud data: %v", err), http.StatusInternalServerError)
			return
		}

		fmt.Printf("Successfully retrieved %d cloud data records\n", len(cloudData))

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(cloudData)
	}
}

func main() {
	db, err := connectDB()
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	fmt.Println("Successfully connected to database!")

	// Initialize repositories
	placeRepo := repository.NewPlaceRepository(db)
	actualScoreRepo := repository.NewActualScoreRepository(db)
	predictedScoreRepo := repository.NewPredictedScoreRepository(db)
	weatherRepo := repository.NewWeatherRepository(db)
	cloudDataRepo := repository.NewCloudDataRepository(db)

	places, err := placeRepo.GetAllPlaces()
	if err != nil {
		log.Fatal("Failed to get places:", err)
	}

	fmt.Printf("Found %d places:\n", len(places))
	for _, place := range places {
		fmt.Printf("- %s (ID: %d)\n", place.Name, place.ID)
		fmt.Printf("%+v\n", place)

		actualScores, err := actualScoreRepo.GetActualScoresByPlace(place.ID)
		if err != nil {
			log.Printf("Failed to get actual scores for place %d: %v", place.ID, err)
		} else {
			fmt.Printf("  Actual scores: %d records\n", len(actualScores))
			fmt.Printf("%+v\n", actualScores)
		}

		predictedScores, err := predictedScoreRepo.GetPredictedScoresByPlace(place.ID)
		if err != nil {
			log.Printf("Failed to get predicted scores for place %d: %v", place.ID, err)
		} else {
			fmt.Printf("  Predicted scores: %d records\n", len(predictedScores))
			fmt.Printf("%+v\n", predictedScores)
		}
	}

	weather, err := weatherRepo.GetLatestWeather()
	if err != nil {
		log.Fatal("Failed to get weather:", err)
	}
	fmt.Printf("Latest weather records: %d\n", len(weather))
	fmt.Printf("%+v\n", weather)

	// Setup HTTP server
	r := mux.NewRouter()
	r.HandleFunc("/api/cloud-data/{placeID}/{targetDate}", getCloudDataByDateHandler(cloudDataRepo)).Methods("GET")

	fmt.Println("Server starting on :8080")
	fmt.Println("Test endpoint: http://localhost:8080/api/cloud-data/1/2025-07-05")
	log.Fatal(http.ListenAndServe(":8080", r))
}
