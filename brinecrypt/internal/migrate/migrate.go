package migrate

import (
	"brinecrypt/internal/orm"

	"gorm.io/gorm"
)

func Migrate(db *gorm.DB) error {
	return db.AutoMigrate(
		&orm.Namespace{},
		&orm.EncryptionKey{},
		&orm.Resource{},
		&orm.ResourceValue{},
	)
}
