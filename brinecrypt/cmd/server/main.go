package main

import (
	"net/http"
	"os"

	"brinecrypt/internal/api"
	"brinecrypt/internal/migrate"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	dsn := os.Getenv("DATABASE_URL")
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic(err)
	}

	if err := migrate.Migrate(db); err != nil {
		panic(err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/{namespace}/{name}", api.GetResource(db))
	mux.HandleFunc("PUT /api/v1/{namespace}/{name}", api.PutResource(db))
	mux.HandleFunc("GET /api/v1/{namespace}/{name}/versions", api.ListResourceVersions(db))
	mux.HandleFunc("GET /api/v1/{namespace}/{name}/{version}", api.GetResourceByVersion(db))
	mux.HandleFunc("GET /api/v1/{uuid}", api.GetResourceValue(db))

	http.ListenAndServe(":8080", mux)
}
