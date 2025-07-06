package repository

import (
	"crowdsense/backend/model"
)

type PlaceRepository interface {
	GetAllPlaces() ([]model.Place, error)
}

type ActualScoreRepository interface {
	GetActualScoresByPlace(placeID int) ([]model.ActualScore, error)
}

type PredictedScoreRepository interface {
	GetPredictedScoresByPlace(placeID int) ([]model.PredictedScore, error)
}

type WeatherRepository interface {
	GetLatestWeather() ([]model.Weather, error)
}

type CloudDataRepository interface {
	GetCloudDataByDate(placeID int, targetDate string) ([]model.CloudData, error)
}