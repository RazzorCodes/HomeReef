package api

import (
	"encoding/json"
	"net/http"
	"strconv"
	"fmt"

	"brinecrypt/internal/orm"
	"brinecrypt/internal/store"
	"gorm.io/gorm"
)

func GetResourceValue(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uuid := r.PathValue("uuid")

		rv, err := store.GetResourceValueByUUID(db, uuid)
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

func GetResource(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

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
		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

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

		var versionsSummary []ResourceValueSummary
		for _, v := range versions {
			versionsSummary = append(versionsSummary, SummarizeResourceValue(v))
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(versionsSummary)
	}
}

func ListResourcesInNamespace(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		namespace := r.PathValue("namespace")
		resources, err := store.ListResources(db, namespace)
		if err != nil {
			http.Error(w, "internal server error", http.StatusInternalServerError)
			return
		}

		var summary []ResourceSummary
		for _, resource := range resources {
			s := SummarizeResource(resource)
			summary = append(summary, s)
		}
		fmt.Println(summary)

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(summary)
	}
}

func GetResourceByVersion(db *gorm.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		namespace := r.PathValue("namespace")
		name := r.PathValue("name")
		versionStr := r.PathValue("version")

		version, err := strconv.ParseUint(versionStr, 10, 64)
		if err != nil {
			http.Error(w, "invalid version number", http.StatusBadRequest)
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
		namespace := r.PathValue("namespace")
		name := r.PathValue("name")

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
