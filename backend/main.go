package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
	"github.com/Maxel31/Congestion-Watch/backend/model"
	"github.com/Maxel31/Congestion-Watch/backend/repository"
)


func connectDB() (*sql.DB, error) {
	// Docker環境では環境変数を直接使用するため、.envファイルの読み込みは不要
	_ = godotenv.Load() // エラーを無視

	host := os.Getenv("POSTGRES_HOST")
	port := os.Getenv("POSTGRES_PORT")
	user := os.Getenv("POSTGRES_USER")
	password := os.Getenv("POSTGRES_PASSWORD")
	dbname := os.Getenv("POSTGRES_DB")

	if host == "" {
		host = "localhost"
	}
	if port == "" {
		port = "5432"
	}

	psqlInfo := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

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
	fmt.Printf("\nLatest weather records: %d\n", len(weather))
	fmt.Printf("%+v\n", weather)

	// 特定の日にちのcloud_dataを取得
	targetDate := "2025-07-05"
	cloudData, err := cloudDataRepo.GetCloudDataByDate(targetDate)
	if err != nil {
		log.Fatal("Failed to get cloud data:", err)
	}
	fmt.Printf("\nCloud data for %s: %d records\n", targetDate, len(cloudData))
	for _, cd := range cloudData {
		fmt.Printf("Place ID: %d, Time: %s", cd.PlaceID, cd.TargetDatetime.Format("2006-01-02 15:04:05"))
		if cd.ActualScore != nil {
			fmt.Printf(", Actual: %d", *cd.ActualScore)
		}
		if cd.PredictedScore != nil {
			fmt.Printf(", Predicted: %d", *cd.PredictedScore)
		}
		fmt.Println()
	}
}
