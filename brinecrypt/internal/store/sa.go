package store

import (
	"time"

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

func GetOrCreateSA(db *gorm.DB, namespace, name string) (*orm.SA, error) {
	sa, err := GetSA(db, namespace, name)
	if err == gorm.ErrRecordNotFound {
		sa = &orm.SA{Namespace: namespace, Name: name, SyncedAt: time.Now()}
		if err = CreateSA(db, sa); err != nil {
			return nil, err
		}
		return sa, nil
	}
	return sa, err
}
