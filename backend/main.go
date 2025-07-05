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

type CloudData struct {
	PredictedScore *int      `json:"predicted_score"`
	ActualScore    *int      `json:"actual_score"`
	TargetDatetime time.Time `json:"target_datetime"`
	PlaceID        int       `json:"place_id"`
}

type CongestionData struct {
	PlaceID          int       `json:"place_id"`
	PlaceName        string    `json:"place_name"`
	TargetDatetime   time.Time `json:"target_datetime"`
	ActualScore      *int      `json:"actual_score"`
	PredictedScore   *int      `json:"predicted_score"`
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

func getCloudDataByDate(db *sql.DB, targetDate string) ([]CloudData, error) {
	query := `
		SELECT 
			ps.score as predicted_score,
			acs.score as actual_score,
			ps.target_datetime,
			ps.place_id
		FROM (
			SELECT DISTINCT ON (place_id, target_datetime)
				place_id,
				target_datetime,
				score
			FROM predicted_score
			WHERE DATE(target_datetime) = DATE($1)
			ORDER BY place_id, target_datetime, created_at DESC
		) ps
		LEFT JOIN actual_score acs
			ON ps.place_id = acs.place_id 
			AND ps.target_datetime = acs.target_datetime
		ORDER BY ps.place_id, ps.target_datetime
	`
	
	rows, err := db.Query(query, targetDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var cloudData []CloudData
	for rows.Next() {
		var cd CloudData
		var predictedScore, actualScore sql.NullInt64
		err := rows.Scan(&predictedScore, &actualScore, &cd.TargetDatetime, &cd.PlaceID)
		if err != nil {
			return nil, err
		}
		
		if predictedScore.Valid {
			score := int(predictedScore.Int64)
			cd.PredictedScore = &score
		}
		if actualScore.Valid {
			score := int(actualScore.Int64)
			cd.ActualScore = &score
		}
		
		cloudData = append(cloudData, cd)
	}
	return cloudData, nil
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
    fmt.Printf("%+v\n", place)
		
		actualScores, err := getActualScoresByPlace(db, place.ID)
		if err != nil {
			log.Printf("Failed to get actual scores for place %d: %v", place.ID, err)
		} else {
			fmt.Printf("  Actual scores: %d records\n", len(actualScores))
      fmt.Printf("%+v\n", actualScores)
		}

		predictedScores, err := getPredictedScoresByPlace(db, place.ID)
		if err != nil {
			log.Printf("Failed to get predicted scores for place %d: %v", place.ID, err)
		} else {
			fmt.Printf("  Predicted scores: %d records\n", len(predictedScores))
      fmt.Printf("%+v\n", predictedScores)
		}
	}

	weather, err := getLatestWeather(db)
	if err != nil {
		log.Fatal("Failed to get weather:", err)
	}
	fmt.Printf("\nLatest weather records: %d\n", len(weather))
	fmt.Printf("%+v\n", weather)

	// 特定の日にちのcloud_dataを取得
	targetDate := "2025-07-05"
	cloudData, err := getCloudDataByDate(db, targetDate)
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
