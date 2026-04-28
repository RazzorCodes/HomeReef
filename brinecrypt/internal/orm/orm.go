package orm

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
)

type Namespace struct {
	Id        uint      `gorm:"primaryKey" json:"-"`
	Name      string    `gorm:"column:name" json:"name"`
	CreatedAt time.Time `gorm:"column:created_at" json:"created_at"`
}

func (Namespace) TableName() string {
	return "namespaces"
}

type ResourceType int

const (
	ResourceTypeUndefined ResourceType = 0
	ResourceTypeCleartext ResourceType = 1
	ResourceTypeEncrypted ResourceType = 2
)

var resourceTypeNames = map[ResourceType]string{
	ResourceTypeUndefined: "undefined",
	ResourceTypeCleartext: "cleartext",
	ResourceTypeEncrypted: "encrypted",
}

var resourceTypeValues = map[string]ResourceType{
	"undefined": ResourceTypeUndefined,
	"cleartext": ResourceTypeCleartext,
	"encrypted": ResourceTypeEncrypted,
}

func (t ResourceType) MarshalJSON() ([]byte, error) {
	s, ok := resourceTypeNames[t]
	if !ok {
		return nil, fmt.Errorf("unknown ResourceType %d", t)
	}
	return json.Marshal(s)
}

func (t *ResourceType) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}
	v, ok := resourceTypeValues[s]
	if !ok {
		return fmt.Errorf("unknown ResourceType %q", s)
	}
	*t = v
	return nil
}

type Resource struct {
	Id          uint         `gorm:"primaryKey" json:"-"`
	NamespaceId uint         `gorm:"column:namespace_id" json:"-"`
	Namespace   Namespace    `gorm:"foreignKey:NamespaceId" json:"namespace,omitempty"`
	Name        string       `gorm:"column:name" json:"name"`
	Type        ResourceType `gorm:"column:resource_type" json:"type"`
	CreatedAt   time.Time    `gorm:"column:created_at" json:"created_at"`
	CreatedBy   string       `gorm:"column:created_by" json:"created_by"`
	RetiredAt   *time.Time   `gorm:"column:retired_at" json:"retired_at,omitempty"`

	Value    *ResourceValue  `gorm:"foreignKey:ResourceId" json:"value,omitempty"`
	Versions []ResourceValue `gorm:"foreignKey:ResourceId" json:"versions,omitempty"`
}

func (Resource) TableName() string {
	return "resources"
}

type EncryptionType int

const (
	EncryptionTypeUndefined EncryptionType = 0
	EncryptionTypeAES256GCM EncryptionType = 1
)

var encryptionTypeNames = map[EncryptionType]string{
	EncryptionTypeUndefined: "undefined",
	EncryptionTypeAES256GCM: "aes-256-gcm",
}

var encryptionTypeValues = map[string]EncryptionType{
	"undefined":   EncryptionTypeUndefined,
	"aes-256-gcm": EncryptionTypeAES256GCM,
}

func (t EncryptionType) MarshalJSON() ([]byte, error) {
	s, ok := encryptionTypeNames[t]
	if !ok {
		return nil, fmt.Errorf("unknown EncryptionType %d", t)
	}
	return json.Marshal(s)
}

func (t *EncryptionType) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}
	v, ok := encryptionTypeValues[s]
	if !ok {
		return fmt.Errorf("unknown EncryptionType %q", s)
	}
	*t = v
	return nil
}

type EncryptionKey struct {
	Id           uint      `gorm:"primaryKey" json:"id"`
	EncryptedDEK string    `gorm:"column:encrypted_dek" json:"encrypted_dek"`
	KekVersion   uint      `gorm:"column:kek_version" json:"kek_version"`
	CreatedAt    time.Time `gorm:"column:created_at" json:"created_at"`
}

func (EncryptionKey) TableName() string {
	return "encryption_keys"
}

type ResourceValue struct {
	Uuid            uuid.UUID      `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"uuid"`
	ResourceId      uint           `gorm:"column:resource_id" json:"resource_id"`
	Version         uint           `gorm:"column:version" json:"version"`
	Data            string         `gorm:"column:data" json:"data"`
	EncryptedBy     EncryptionType `gorm:"column:encrypted_by" json:"encrypted_by"`
	EncryptionKeyId *uint          `gorm:"column:encryption_key_id" json:"encryption_key_id,omitempty"`
	EncryptionKey   *EncryptionKey `gorm:"foreignKey:EncryptionKeyId" json:"encryption_key,omitempty"`
	CreatedAt       time.Time      `gorm:"column:created_at" json:"created_at"`
	RetiredAt       *time.Time     `gorm:"column:retired_at" json:"retired_at,omitempty"`
}

func (ResourceValue) TableName() string {
	return "resource_versions"
}
