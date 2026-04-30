package auth

import (
	"context"
	"fmt"
	"net/http"
	"strings"
	"time"

	"brinecrypt/internal/orm"
	"brinecrypt/internal/store"

	"gorm.io/gorm"
)

const (
	SessionPrefix = "sess_"
	RefreshPrefix = "refr_"
)

type contextKey string

const UserContextKey contextKey = "user"

func AuthMiddleware(db *gorm.DB, next http.Handler) http.Handler {
	public := map[string]bool{
		"/auth/login":        true,
		"/admin/users":       true,
		"/admin/permissions": true,
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if public[r.URL.Path] {
			next.ServeHTTP(w, r)
			return
		}
		raw := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		if raw == "" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		var (
			user *orm.User
			err  error
		)

		switch {
		case strings.HasPrefix(raw, SessionPrefix):
			user, err = resolveSession(db, raw)
		// TODO: case strings.HasPrefix(raw, "pat_"): user, err = resolvePAT(db, raw)
		// TODO: SA JWT: user, err = resolveSAJWT(db, raw)
		default:
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		if err != nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		ctx := context.WithValue(r.Context(), UserContextKey, user)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func resolveSession(db *gorm.DB, token string) (*orm.User, error) {
	session, err := store.GetSessionByTokenHash(db, HashToken(token))
	if err != nil {
		return nil, err
	}
	if time.Now().After(session.ExpiresAt) {
		return nil, fmt.Errorf("session expired")
	}
	return store.GetUserById(db, session.UserId)
}

