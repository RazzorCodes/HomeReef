package api

import (
	"brinecrypt/internal/orm"
	"time"

	"github.com/google/uuid"
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
	Uuid            uuid.UUID      `json:"uuid"`
	Version         uint           `json:"version"`
	CreatedBy		string `json"created_by"`
	CreatedAt       time.Time      `json:"created_at"`
	RetiredAt       *time.Time     `json:"retired_at,omitempty"`
	EncryptionAlgorithm     orm.EncryptionAlgorithm
}

func SummarizeResourceValue (r orm.ResourceValue) ResourceValueSummary {
	return ResourceValueSummary{
          Uuid:      r.Uuid,
          Version:      r.Version,

          CreatedAt: r.CreatedAt,
          CreatedBy: r.CreatedBy,
          RetiredAt: r.RetiredAt,

          EncryptionAlgorithm: r.EncryptionAlgorithm,
      }
}
