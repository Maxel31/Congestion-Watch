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
				predicted_score,
				actual_score,
				target_datetime,
				place_id
		FROM cloud_data
		WHERE place_id = $1 AND target_datetime::date = $2;
	`

	rows, err := r.db.Query(query, placeID, targetDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var cloudData = make([]model.CloudData, 0)
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
