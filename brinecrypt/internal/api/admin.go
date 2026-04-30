package api

import (
	"encoding/json"
	"net/http"
	"time"

	"brinecrypt/internal/authz"
	"brinecrypt/internal/logger"
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
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		hash, err := bcrypt.GenerateFromPassword([]byte(body.Pass), bcrypt.DefaultCost)
		if err != nil {
			logger.Error("bcrypt failed: " + err.Error())
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		u := &orm.User{
			Name:  body.Name,
			Email: body.Email,
			Pass:  string(hash),
		}
		if err := store.CreateUser(db, u); err != nil {
			logger.Error("create user failed: " + err.Error())
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}

type permissionEntry struct {
	Verb            orm.Verb   `json:"verb"`
	ResourcePattern string     `json:"resource_pattern"`
	ExpiresAt       *time.Time `json:"expires_at,omitempty"`
}

type permissionsRequestBody struct {
	Principal   string            `json:"principal"`
	Permissions []permissionEntry `json:"permissions"`
}

func GrantPermissions(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var body permissionsRequestBody
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			logger.Error("grant permissions decode failed: " + err.Error())
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		if body.Principal == "" || len(body.Permissions) == 0 {
			logger.Warn("grant permissions: missing principal or permissions")
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		principal, err := authz.ParsePrincipal(body.Principal)
		if err != nil {
			logger.Warn("invalid principal: " + err.Error())
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		for _, entry := range body.Permissions {
			if err := authz.ValidateAddPattern(entry.ResourcePattern); err != nil {
				logger.Warn("invalid pattern: " + err.Error())
				http.Error(w, "bad request", http.StatusBadRequest)
				return
			}
		}

		var principalID uint
		switch principal.Kind {
		case authz.PrincipalUser:
			u, err := store.GetUser(db, principal.Name)
			if err != nil {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			principalID = u.Id
		case authz.PrincipalSA:
			sa, err := store.GetSA(db, principal.SANamespace, principal.SAName)
			if err != nil {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			principalID = sa.Id
		}

		for _, entry := range body.Permissions {
			p := &orm.Permission{
				ResourcePattern: entry.ResourcePattern,
				Verb:            entry.Verb,
				ExpiresAt:       entry.ExpiresAt,
			}
			if err := store.CreatePermission(db, p); err != nil {
				logger.Error("create permission failed: " + err.Error())
				http.Error(w, "internal server error", http.StatusInternalServerError)
				return
			}
			switch principal.Kind {
			case authz.PrincipalUser:
				err = store.AddPermissionToUser(db, principalID, p.Id)
			case authz.PrincipalSA:
				err = store.AddPermissionToSA(db, principalID, p.Id)
			}
			if err != nil {
				logger.Error("link permission failed: " + err.Error())
				http.Error(w, "internal server error", http.StatusInternalServerError)
				return
			}
		}

		w.WriteHeader(http.StatusNoContent)
	}
}

func RevokePermissions(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var body permissionsRequestBody
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			logger.Error("revoke permissions decode failed: " + err.Error())
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		if body.Principal == "" || len(body.Permissions) == 0 {
			logger.Warn("revoke permissions: missing principal or permissions")
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		principal, err := authz.ParsePrincipal(body.Principal)
		if err != nil {
			logger.Warn("invalid principal: " + err.Error())
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}

		for _, entry := range body.Permissions {
			if err := authz.ValidateDeletePattern(entry.ResourcePattern); err != nil {
				logger.Warn("invalid pattern: " + err.Error())
				http.Error(w, "bad request", http.StatusBadRequest)
				return
			}
		}

		var principalID uint
		switch principal.Kind {
		case authz.PrincipalUser:
			u, err := store.GetUser(db, principal.Name)
			if err != nil {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			principalID = u.Id
		case authz.PrincipalSA:
			sa, err := store.GetSA(db, principal.SANamespace, principal.SAName)
			if err != nil {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			principalID = sa.Id
		}

		for _, entry := range body.Permissions {
			switch principal.Kind {
			case authz.PrincipalUser:
				err = store.RevokeMatchingPermissionsFromUser(db, principalID, entry.Verb, entry.ResourcePattern)
			case authz.PrincipalSA:
				err = store.RevokeMatchingPermissionsFromSA(db, principalID, entry.Verb, entry.ResourcePattern)
			}
			if err != nil {
				logger.Error("revoke permission failed: " + err.Error())
				http.Error(w, "internal server error", http.StatusInternalServerError)
				return
			}
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
