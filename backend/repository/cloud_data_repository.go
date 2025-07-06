package repository

import (
	"crowdsense/backend/model"
	"database/sql"
)

type cloudDataRepository struct {
	db *sql.DB
}

func NewCloudDataRepository(db *sql.DB) CloudDataRepository {
	return &cloudDataRepository{db: db}
}

func (r *cloudDataRepository) GetCloudDataByDate(placeID int, targetDate string) ([]model.CloudData, error) {
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
			WHERE place_id = $1 AND DATE(target_datetime) = DATE($2)
			ORDER BY place_id, target_datetime, created_at DESC
		) ps
		LEFT JOIN actual_score acs
			ON ps.place_id = acs.place_id 
			AND ps.target_datetime = acs.target_datetime
		ORDER BY ps.target_datetime DESC, ps.place_id, ps.score DESC
	`

	rows, err := r.db.Query(query, placeID, targetDate)
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
