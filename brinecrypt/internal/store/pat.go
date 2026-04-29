package store

import (
	"brinecrypt/internal/orm"

	"gorm.io/gorm"
)

func CreatePAT(db *gorm.DB, pat *orm.PAT) error {
	return db.Create(pat).Error
}

func GetPATByTokenHash(db *gorm.DB, tokenHash string) (*orm.PAT, error) {
	var pat orm.PAT
	err := db.Where("token_hash = ?", tokenHash).First(&pat).Error
	return &pat, err
}

func DeletePAT(db *gorm.DB, id uint) error {
	return db.Delete(&orm.PAT{}, id).Error
}
