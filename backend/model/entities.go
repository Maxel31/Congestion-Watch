package model

import "time"

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