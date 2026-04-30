package api

import (
	"encoding/json"
	"net/http"
	"strconv"
	"time"

	"brinecrypt/internal/auth"
	"brinecrypt/internal/authz"
	"brinecrypt/internal/orm"
	"brinecrypt/internal/store"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type ResourceSummary struct {
	Name      string           `json:"name"`
	Type      orm.ResourceType `json:"type"`
	CreatedAt time.Time        `json:"created_at"`
	CreatedBy string           `json:"created_by"`
	RetiredAt *time.Time       `json:"retired_at,omitempty"`
}

func SummarizeResource(r orm.Resource) ResourceSummary {
	return ResourceSummary{
		Name:      r.Name,
		Type:      r.Type,
		CreatedAt: r.CreatedAt,
		CreatedBy: r.CreatedBy,
		RetiredAt: r.RetiredAt,
	}
}

type ResourceValueSummary struct {
	Uuid                uuid.UUID               `json:"uuid"`
	Version             uint                    `json:"version"`
	CreatedBy           string                  `json:"created_by"`
	CreatedAt           time.Time               `json:"created_at"`
	RetiredAt           *time.Time              `json:"retired_at,omitempty"`
	EncryptionAlgorithm orm.EncryptionAlgorithm `json:"encryption_algorithm"`
}

func SummarizeResourceValue(r orm.ResourceValue) ResourceValueSummary {
	return ResourceValueSummary{
		Uuid:                r.Uuid,
		Version:             r.Version,
		CreatedAt:           r.CreatedAt,
		CreatedBy:           r.CreatedBy,
		RetiredAt:           r.RetiredAt,
		EncryptionAlgorithm: r.EncryptionAlgorithm,
	}
}

func principalFromContext(r *http.Request) (*authz.Principal, bool) {
	user, ok := r.Context().Value(auth.UserContextKey).(*orm.User)
	if !ok {
		return nil, false
	}
	return authz.NewPrincipalFromUser(user), true
}

func GetResourceValue(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		uuidStr := r.PathValue("uuid")
		rv, err := store.GetResourceValueByUUID(db, uuidStr)
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		resource, err := store.GetResourceByID(db, rv.ResourceId)
		if err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		allowed, err := authz.Check(db, principal, orm.VerbTypeRead, resource.Namespace.Name, resource.Name)
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(rv)
	}
}

func GetResource(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

		allowed, err := authz.Check(db, principal, orm.VerbTypeRead, namespace, name)
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		resource, err := store.GetResource(db, namespace, name)
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resource)
	}
}

func ListResourceVersions(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

		allowed, err := authz.Check(db, principal, orm.VerbTypeList, namespace, name)
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		resource, err := store.GetResource(db, namespace, name)
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		versions, err := store.ListResourceVersions(db, resource.Id)
		if err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		var summary []ResourceValueSummary
		for _, v := range versions {
			summary = append(summary, SummarizeResourceValue(v))
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(summary)
	}
}

func ListResourcesInNamespace(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		namespace := r.PathValue("namespace")

		allowed, err := authz.Check(db, principal, orm.VerbTypeList, namespace, "*")
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		resources, err := store.ListResources(db, namespace)
		if err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		var summary []ResourceSummary
		for _, resource := range resources {
			summary = append(summary, SummarizeResource(resource))
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(summary)
	}
}

func GetResourceByVersion(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		namespace := r.PathValue("namespace")
		name := r.PathValue("name")
		versionStr := r.PathValue("version")

		version, err := strconv.ParseUint(versionStr, 10, 64)
		if err != nil {
			http.Error(w, "invalid version number", http.StatusBadRequest)
			return
		}

		allowed, err := authz.Check(db, principal, orm.VerbTypeRead, namespace, name)
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		resource, err := store.GetResource(db, namespace, name)
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		rv, err := store.GetResourceVersion(db, resource.Id, uint(version))
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(rv)
	}
}

func DeleteResource(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

		allowed, err := authz.Check(db, principal, orm.VerbTypeDelete, namespace, name)
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		if err := store.DeleteResource(db, namespace, name); err != nil {
			if err == gorm.ErrRecordNotFound {
				http.Error(w, "not found", http.StatusNotFound)
				return
			}
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}

func PutResource(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		principal, ok := principalFromContext(r)
		if !ok {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

		var body struct {
			Type  orm.ResourceType `json:"type"`
			Value string           `json:"value"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "invalid request body", http.StatusBadRequest)
			return
		}

		allowed, err := authz.Check(db, principal, orm.VerbTypeWrite, namespace, name)
		if err != nil || !allowed {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		ns, err := store.GetNamespace(db, namespace)
		if err != nil {
			if err == gorm.ErrRecordNotFound {
				ns, err = store.CreateNamespace(db, namespace)
				if err != nil {
					http.Error(w, "internal server error", http.StatusInternalServerError)
					return
				}
			} else {
				http.Error(w, "internal server error", http.StatusInternalServerError)
				return
			}
		}

		resource, err := store.GetResource(db, namespace, name)
		if err != nil && err != gorm.ErrRecordNotFound {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		if err == gorm.ErrRecordNotFound {
			resource = &orm.Resource{
				NamespaceId: ns.Id,
				Name:        name,
				Type:        body.Type,
			}
			if err := store.CreateResource(db, resource); err != nil {
				http.Error(w, "internal server error", http.StatusInternalServerError)
				return
			}
		}

		rv := &orm.ResourceValue{
			ResourceId: resource.Id,
			Data:       body.Value,
		}
		if err := store.CreateResourceValue(db, rv); err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
