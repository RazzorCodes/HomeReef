package store

import (
	"brinecrypt/internal/orm"

	"gorm.io/gorm"
)

func GetUser(db *gorm.DB, name string) (*orm.User, error) {
	var u orm.User
	err := db.Where("name = ?", name).First(&u).Error
	return &u, err
}

func GetUserById(db *gorm.DB, id uint) (*orm.User, error) {
	var u orm.User
	err := db.First(&u, id).Error
	return &u, err
}

func CreateUser(db *gorm.DB, u *orm.User) error {
	return db.Create(u).Error
}
