package repository

import (
	"database/sql"
	"github.com/Maxel31/Congestion-Watch/backend/model"
)

type cloudDataRepository struct {
	db *sql.DB
}

func NewCloudDataRepository(db *sql.DB) CloudDataRepository {
	return &cloudDataRepository{db: db}
}

func (r *cloudDataRepository) GetCloudDataByDate(targetDate string) ([]model.CloudData, error) {
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
	
	rows, err := r.db.Query(query, targetDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var cloudData []model.CloudData
	for rows.Next() {
		var cd model.CloudData
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