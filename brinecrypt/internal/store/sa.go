package store

import (
	"brinecrypt/internal/orm"

	"gorm.io/gorm"
)

func GetSA(db *gorm.DB, namespace string, name string) (*orm.SA, error) {
	var sa orm.SA
	err := db.Where("sa_namespace = ? AND sa_name = ?", namespace, name).First(&sa).Error
	return &sa, err
}

func CreateSA(db *gorm.DB, sa *orm.SA) error {
	return db.Create(sa).Error
}
