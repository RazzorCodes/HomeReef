package api

import (
	"brinecrypt/internal/auth"
	"brinecrypt/internal/orm"
	"brinecrypt/internal/store"
	"time"

	"gorm.io/gorm"
)

func NewSession(db *gorm.DB, u *orm.User) (*LoginResponseBody, error) {
	st, err := auth.GenerateToken()
	if err != nil {
		return nil, err
	}
	rt, err := auth.GenerateToken()
	if err != nil {
		return nil, err
	}

	s := orm.Session{
		UserId:           u.Id,
		TokenHash:        auth.HashToken(st),
		RefreshTokenHash: auth.HashToken(rt),
		CreatedAt:        time.Now(),
		ExpiresAt:        time.Now().Add(15 * time.Minute),
	}

	err = store.CreateSession(db, &s)
	if err != nil {
		return nil, err
	}

	return &LoginResponseBody{
		SessionToken: st,
		RefreshToken: rt,
	}, nil
}
