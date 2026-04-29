package store

import (
	"brinecrypt/internal/orm"

	"gorm.io/gorm"
)

func CreateSession(db *gorm.DB, s *orm.Session) error {
	return db.Create(s).Error
}

func GetSessionByTokenHash(db *gorm.DB, tokenHash string) (*orm.Session, error) {
	var s orm.Session
	err := db.Where("token_hash = ?", tokenHash).First(&s).Error
	return &s, err
}

func GetSessionByRefreshTokenHash(db *gorm.DB, refreshTokenHash string) (*orm.Session, error) {
	var s orm.Session
	err := db.Where("refresh_token_hash = ?", refreshTokenHash).First(&s).Error
	return &s, err
}

func UpdateSessionTokens(db *gorm.DB, id uint, tokenHash string, refreshTokenHash string) error {
	return db.Model(&orm.Session{}).Where("id = ?", id).Updates(map[string]any{
		"token_hash":         tokenHash,
		"refresh_token_hash": refreshTokenHash,
	}).Error
}

func DeleteSession(db *gorm.DB, id uint) error {
	return db.Delete(&orm.Session{}, id).Error
}
