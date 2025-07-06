package repository

import (
	"database/sql"
	"github.com/Maxel31/Congestion-Watch/backend/model"
)

type placeRepository struct {
	db *sql.DB
}

func NewPlaceRepository(db *sql.DB) PlaceRepository {
	return &placeRepository{db: db}
}

func (r *placeRepository) GetAllPlaces() ([]model.Place, error) {
	query := "SELECT id, name, created_at FROM place ORDER BY id"
	rows, err := r.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var places []model.Place
	for rows.Next() {
		var p model.Place
		err := rows.Scan(&p.ID, &p.Name, &p.CreatedAt)
		if err != nil {
			return nil, err
		}
		places = append(places, p)
	}
	return places, nil
}