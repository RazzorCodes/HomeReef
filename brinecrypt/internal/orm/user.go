package orm

import "time"

type User struct {
	Id        uint      `gorm:"primaryKey" json:"-"`
	Name      string    `gorm:"column:name" json:"name"`
	Email     string    `gorm:"column:email" json:"email,omitempty"`
	Pass      string    `gorm:"column:pass" json:"-"`
	CreatedAt time.Time `gorm:"column:created_at" json:"created_at"`
}

func (User) TableName() string {
	return "users"
}
