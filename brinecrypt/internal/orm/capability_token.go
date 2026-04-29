package orm

import "time"

type CapabilityToken struct {
	Id                uint       `gorm:"primaryKey" json:"-"`
	IssuedBy          *uint      `gorm:"column:issued_by" json:"-"`
	Issuer            *User      `gorm:"foreignKey:IssuedBy" json:"-"`
	ResourceNamespace string     `gorm:"column:resource_namespace" json:"resource_namespace"`
	ResourceName      string     `gorm:"column:resource_name" json:"resource_name"`
	Verbs             string     `gorm:"column:verbs" json:"verbs"`
	TokenHash         string     `gorm:"column:token_hash" json:"-"`
	Expiry            *time.Time `gorm:"column:expiry" json:"expiry,omitempty"`
	CreatedAt         time.Time  `gorm:"column:created_at" json:"created_at"`
}

func (CapabilityToken) TableName() string {
	return "capability_tokens"
}
