package repository

import (
	"database/sql"
	"crowdsense/backend/model"
)

type weatherRepository struct {
	db *sql.DB
}

func NewWeatherRepository(db *sql.DB) WeatherRepository {
	return &weatherRepository{db: db}
}

func (r *weatherRepository) GetLatestWeather() ([]model.Weather, error) {
	query := `
		SELECT id, datetime, weather, created_at 
		FROM weather 
		ORDER BY datetime DESC 
		LIMIT 10
	`
	rows, err := r.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var weather []model.Weather
	for rows.Next() {
		var w model.Weather
		err := rows.Scan(&w.ID, &w.Datetime, &w.Weather, &w.CreatedAt)
		if err != nil {
			return nil, err
		}
		weather = append(weather, w)
	}
	return weather, nil
}