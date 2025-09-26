// models/user.go
package models

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"golang.org/x/crypto/bcrypt"
	"log"
	"regexp"
	"time"
)

type User struct {
	ID                uint      `json:"id" gorm:"primaryKey"`
	Username          string    `json:"username" gorm:"unique;not null" validate:"required,min=3,max=30"`
	Email             string    `json:"email" gorm:"unique;not null" validate:"required,email"`
	Password          string    `json:"-" gorm:"not null"` // 不返回给前端
	ResetToken        string    `json:"-" gorm:"default:null"`        // 密码重置令牌
	ResetTokenExpiry  *time.Time `json:"-" gorm:"default:null"`        // 令牌过期时间
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

// SetPassword 加密密码
func (u *User) SetPassword(password string) error {
	hashed, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	u.Password = string(hashed)
	return nil
}

// CheckPassword 检查密码
func (u *User) CheckPassword(password string) bool {
	// 确保密码字段不为空
	if u.Password == "" {
		log.Printf("错误: 用户密码哈希为空")
		return false
	}
	
	// 使用bcrypt验证密码
	err := bcrypt.CompareHashAndPassword([]byte(u.Password), []byte(password))
	if err != nil {
		log.Printf("密码验证失败: %v", err)
		return false
	}
	
	log.Printf("密码验证成功")
	return true
}

// GenerateResetToken 生成密码重置令牌
func (u *User) GenerateResetToken() error {
	// 生成32字节的随机token
	bytes := make([]byte, 32)
	if _, err := rand.Read(bytes); err != nil {
		return err
	}
	u.ResetToken = hex.EncodeToString(bytes)
	
	// 设置过期时间为1小时后
	expiryTime := time.Now().Add(time.Hour)
	u.ResetTokenExpiry = &expiryTime
	
	return nil
}

// ValidateResetToken 验证重置令牌是否有效
func (u *User) ValidateResetToken(token string) bool {
	if u.ResetToken == "" || u.ResetTokenExpiry == nil {
		return false
	}
	
	// 检查令牌是否匹配
	if u.ResetToken != token {
		return false
	}
	
	// 检查令牌是否过期
	if time.Now().After(*u.ResetTokenExpiry) {
		return false
	}
	
	return true
}

// ClearResetToken 清除重置令牌
func (u *User) ClearResetToken() {
	u.ResetToken = ""
	u.ResetTokenExpiry = nil
}

// ValidatePassword 验证密码强度
func ValidatePassword(password string) error {
	if len(password) < 6 {
		return errors.New("密码长度至少需要6个字符")
	}
	if len(password) > 50 {
		return errors.New("密码长度不能超过50个字符")
	}
	return nil
}

// ValidateEmail 验证邮箱格式
func ValidateEmail(email string) error {
	if len(email) == 0 {
		return errors.New("邮箱不能为空")
	}
	
	// 简单的邮箱格式验证
	emailRegex := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	if !emailRegex.MatchString(email) {
		return errors.New("邮箱格式无效")
	}
	
	if len(email) > 254 {
		return errors.New("邮箱长度不能超过254个字符")
	}
	
	return nil
}

// ValidateUsername 验证用户名
func ValidateUsername(username string) error {
	if len(username) < 3 {
		return errors.New("用户名长度至少需要3个字符")
	}
	if len(username) > 30 {
		return errors.New("用户名长度不能超过30个字符")
	}
	
	// 用户名只能包含字母、数字、下划线
	usernameRegex := regexp.MustCompile(`^[a-zA-Z0-9_]+$`)
	if !usernameRegex.MatchString(username) {
		return errors.New("用户名只能包含字母、数字和下划线")
	}
	
	return nil
}
