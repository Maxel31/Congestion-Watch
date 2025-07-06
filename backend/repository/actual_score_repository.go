package repository

import (
	"database/sql"
	"github.com/Maxel31/Congestion-Watch/backend/model"
)

type actualScoreRepository struct {
	db *sql.DB
}

func NewActualScoreRepository(db *sql.DB) ActualScoreRepository {
	return &actualScoreRepository{db: db}
}

func (r *actualScoreRepository) GetActualScoresByPlace(placeID int) ([]model.ActualScore, error) {
	query := `
		SELECT id, score, place_id, target_datetime, created_at 
		FROM actual_score 
		WHERE place_id = $1 
		ORDER BY target_datetime DESC
	`
	rows, err := r.db.Query(query, placeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var scores []model.ActualScore
	for rows.Next() {
		var s model.ActualScore
		err := rows.Scan(&s.ID, &s.Score, &s.PlaceID, &s.TargetDatetime, &s.CreatedAt)
		if err != nil {
			return nil, err
		}
		scores = append(scores, s)
	}
	return scores, nil
}