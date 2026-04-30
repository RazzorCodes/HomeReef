package orm

import (
	"encoding/json"
	"fmt"
	"time"
)

type Verb int

const (
	VerbTypeList   = 0
	VerbTypeRead   = 1
	VerbTypeWrite  = 2
	VerbTypeDelete = 3
)

var verbTypeNames = map[Verb]string{
	VerbTypeList:   "list",
	VerbTypeRead:   "read",
	VerbTypeWrite:  "write",
	VerbTypeDelete: "delete",
}

var verbTypeValues = map[string]Verb{
	"list":   VerbTypeList,
	"read":   VerbTypeRead,
	"write":  VerbTypeWrite,
	"delete": VerbTypeDelete,
}

func (v Verb) MarshalJSON() ([]byte, error) {
	s, ok := verbTypeNames[v]
	if !ok {
		return nil, fmt.Errorf("unknown Verb %d", v)
	}
	return json.Marshal(s)
}

func (v *Verb) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}
	vp, ok := verbTypeValues[s]
	if !ok {
		return fmt.Errorf("unknown ResourceType %q", s)
	}
	*v = vp
	return nil
}

type Permission struct {
	Id              uint       `gorm:"primaryKey" json:"-"`
	ResourcePattern string     `gorm:"column:resource_pattern" json:"resource_pattern"`
	Verb            Verb       `gorm:"column:verb" json:"verb"`
	CreatedAt       time.Time  `gorm:"column:created_at" json:"created_at"`
	ExpiresAt       *time.Time `gorm:"column:expires_at" json:"expires_at,omitempty"`
}

func (Permission) TableName() string {
	return "permissions"
}
