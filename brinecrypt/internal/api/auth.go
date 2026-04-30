package api

import (
	"encoding/json"
	"net/http"
	"strings"

	"brinecrypt/internal/auth"

	"gorm.io/gorm"
)

type LoginRequestBody struct {
	User string `json:"user"`
	Pass string `json:"pass"`
}

type LoginResponseBody struct {
	SessionToken string `json:"session_token"`
	RefreshToken string `json:"refresh_token"`
}

func Login(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var request LoginRequestBody
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil || request.User == "" || request.Pass == "" {
			http.Error(w, "malformed input", http.StatusBadRequest)
			return
		}

		tokens, err := auth.Login(db, request.User, request.Pass)
		if err != nil {
			http.Error(w, "incorrect user or password", http.StatusUnauthorized)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(LoginResponseBody{
			SessionToken: tokens.SessionToken,
			RefreshToken: tokens.RefreshToken,
		})
	}
}

type RefreshSessionRequest struct {
	Token string `json:"token"`
}

func Refresh(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var request RefreshSessionRequest
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil || request.Token == "" {
			http.Error(w, "malformed input", http.StatusBadRequest)
			return
		}

		tokens, err := auth.Refresh(db, request.Token)
		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(LoginResponseBody{
			SessionToken: tokens.SessionToken,
			RefreshToken: tokens.RefreshToken,
		})
	}
}

func Logout(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		if token == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		if err := auth.Logout(db, token); err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
