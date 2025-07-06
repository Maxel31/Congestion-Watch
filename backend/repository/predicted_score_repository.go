package repository

import (
	"database/sql"
	"github.com/Maxel31/Congestion-Watch/backend/model"
)

type predictedScoreRepository struct {
	db *sql.DB
}

func NewPredictedScoreRepository(db *sql.DB) PredictedScoreRepository {
	return &predictedScoreRepository{db: db}
}

func (r *predictedScoreRepository) GetPredictedScoresByPlace(placeID int) ([]model.PredictedScore, error) {
	query := `
		SELECT id, model_id, score, place_id, target_datetime, created_at 
		FROM predicted_score 
		WHERE place_id = $1 
		ORDER BY target_datetime DESC
	`
	rows, err := r.db.Query(query, placeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var scores []model.PredictedScore
	for rows.Next() {
		var s model.PredictedScore
		err := rows.Scan(&s.ID, &s.ModelID, &s.Score, &s.PlaceID, &s.TargetDatetime, &s.CreatedAt)
		if err != nil {
			return nil, err
		}
		scores = append(scores, s)
	}
	return scores, nil
}