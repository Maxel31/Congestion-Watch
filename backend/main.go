package main

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/joho/godotenv"
	_ "github.com/lib/pq"
)

type Place struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
}

type Sensor struct {
	ID        int       `json:"id"`
	PlaceID   int       `json:"place_id"`
	CreatedAt time.Time `json:"created_at"`
}

type PredictionModel struct {
	ID          int       `json:"id"`
	SensorID    int       `json:"sensor_id"`
	ModelParams string    `json:"model_params"`
	CreatedAt   time.Time `json:"created_at"`
}

type ActualScore struct {
	ID             int       `json:"id"`
	Score          int       `json:"score"`
	PlaceID        int       `json:"place_id"`
	TargetDatetime time.Time `json:"target_datetime"`
	CreatedAt      time.Time `json:"created_at"`
}

type PredictedScore struct {
	ID             int       `json:"id"`
	ModelID        int       `json:"model_id"`
	Score          int       `json:"score"`
	PlaceID        int       `json:"place_id"`
	TargetDatetime time.Time `json:"target_datetime"`
	CreatedAt      time.Time `json:"created_at"`
}

type Weather struct {
	ID        int       `json:"id"`
	Datetime  time.Time `json:"datetime"`
	Weather   string    `json:"weather"`
	CreatedAt time.Time `json:"created_at"`
}

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

func getAllPlaces(db *sql.DB) ([]Place, error) {
	rows, err := db.Query("SELECT id, name, created_at FROM place ORDER BY id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var places []Place
	for rows.Next() {
		var p Place
		err := rows.Scan(&p.ID, &p.Name, &p.CreatedAt)
		if err != nil {
			return nil, err
		}
		places = append(places, p)
	}
	return places, nil
}

func getActualScoresByPlace(db *sql.DB, placeID int) ([]ActualScore, error) {
	rows, err := db.Query(`
		SELECT id, score, place_id, target_datetime, created_at 
		FROM actual_score 
		WHERE place_id = $1 
		ORDER BY target_datetime DESC
	`, placeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var scores []ActualScore
	for rows.Next() {
		var s ActualScore
		err := rows.Scan(&s.ID, &s.Score, &s.PlaceID, &s.TargetDatetime, &s.CreatedAt)
		if err != nil {
			return nil, err
		}
		scores = append(scores, s)
	}
	return scores, nil
}

func getPredictedScoresByPlace(db *sql.DB, placeID int) ([]PredictedScore, error) {
	rows, err := db.Query(`
		SELECT id, model_id, score, place_id, target_datetime, created_at 
		FROM predicted_score 
		WHERE place_id = $1 
		ORDER BY target_datetime DESC
	`, placeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var scores []PredictedScore
	for rows.Next() {
		var s PredictedScore
		err := rows.Scan(&s.ID, &s.ModelID, &s.Score, &s.PlaceID, &s.TargetDatetime, &s.CreatedAt)
		if err != nil {
			return nil, err
		}
		scores = append(scores, s)
	}
	return scores, nil
}

func getLatestWeather(db *sql.DB) ([]Weather, error) {
	rows, err := db.Query(`
		SELECT id, datetime, weather, created_at 
		FROM weather 
		ORDER BY datetime DESC 
		LIMIT 10
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var weather []Weather
	for rows.Next() {
		var w Weather
		err := rows.Scan(&w.ID, &w.Datetime, &w.Weather, &w.CreatedAt)
		if err != nil {
			return nil, err
		}
		weather = append(weather, w)
	}
	return weather, nil
}

func main() {
	db, err := connectDB()
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}
	defer db.Close()

	fmt.Println("Successfully connected to database!")

	places, err := getAllPlaces(db)
	if err != nil {
		log.Fatal("Failed to get places:", err)
	}

	fmt.Printf("Found %d places:\n", len(places))
	for _, place := range places {
		fmt.Printf("- %s (ID: %d)\n", place.Name, place.ID)
		
		actualScores, err := getActualScoresByPlace(db, place.ID)
		if err != nil {
			log.Printf("Failed to get actual scores for place %d: %v", place.ID, err)
		} else {
			fmt.Printf("  Actual scores: %d records\n", len(actualScores))
		}

		predictedScores, err := getPredictedScoresByPlace(db, place.ID)
		if err != nil {
			log.Printf("Failed to get predicted scores for place %d: %v", place.ID, err)
		} else {
			fmt.Printf("  Predicted scores: %d records\n", len(predictedScores))
		}
	}

	weather, err := getLatestWeather(db)
	if err != nil {
		log.Fatal("Failed to get weather:", err)
	}
	fmt.Printf("\nLatest weather records: %d\n", len(weather))
}
