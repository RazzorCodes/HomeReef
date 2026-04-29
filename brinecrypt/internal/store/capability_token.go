package store

import (
	"brinecrypt/internal/orm"

	"gorm.io/gorm"
)

func CreateCapabilityToken(db *gorm.DB, ct *orm.CapabilityToken) error {
	return db.Create(ct).Error
}

func GetCapabilityTokenByTokenHash(db *gorm.DB, tokenHash string) (*orm.CapabilityToken, error) {
	var ct orm.CapabilityToken
	err := db.Where("token_hash = ?", tokenHash).First(&ct).Error
	return &ct, err
}

func DeleteCapabilityToken(db *gorm.DB, id uint) error {
	return db.Delete(&orm.CapabilityToken{}, id).Error
}
