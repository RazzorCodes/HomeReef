package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"brinecrypt/internal/auth"
	"brinecrypt/internal/store"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

func Login(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var request LoginRequestBody
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil || request.User == "" || request.Pass == "" {
			http.Error(w, "malformed input", http.StatusBadRequest)
			return
		}

		u, err := store.GetUser(db, request.User)
		if err != nil {
			http.Error(w, "incorrect user or password", http.StatusUnauthorized)
			return
		}

		if err := bcrypt.CompareHashAndPassword([]byte(u.Pass), []byte(request.Pass)); err != nil {
			http.Error(w, "incorrect user or password", http.StatusUnauthorized)
			return
		}

		response, err := NewSession(db, u)
		if err != nil {
			http.Error(w, "could not create session", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

func Refresh(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		if token == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		session, err := store.GetSessionByRefreshTokenHash(db, auth.HashToken(token))
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		u, err := store.GetUserById(db, session.UserId)
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		response, err := NewSession(db, u)
		if err != nil {
			http.Error(w, "could not refresh session", http.StatusInternalServerError)
			return
		}

		if err := store.DeleteSession(db, session.Id); err != nil {
			http.Error(w, "could not refresh session", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}
}

func Logout(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		if token == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		session, err := store.GetSessionByTokenHash(db, auth.HashToken(token))
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		if err := store.DeleteSession(db, session.Id); err != nil {
			http.Error(w, "could not logout", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
