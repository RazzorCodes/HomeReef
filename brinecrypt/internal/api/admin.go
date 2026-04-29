package api

import (
	"encoding/json"
	"net/http"

	"brinecrypt/internal/orm"
	"brinecrypt/internal/store"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

func CreateUser(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Name  string `json:"name"`
			Email string `json:"email"`
			Pass  string `json:"pass"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil || body.Name == "" || body.Pass == "" {
			http.Error(w, "malformed input", http.StatusBadRequest)
			return
		}

		hash, err := bcrypt.GenerateFromPassword([]byte(body.Pass), bcrypt.DefaultCost)
		if err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		u := &orm.User{
			Name:  body.Name,
			Email: body.Email,
			Pass:  string(hash),
		}
		if err := store.CreateUser(db, u); err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
