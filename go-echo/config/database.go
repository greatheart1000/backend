// config/database.go

package config

import (
	"go-echo/models"
	"os"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

var DB *gorm.DB

func Connect() {
	// 使用绝对路径，确保文件能被创建
	dbPath := "./data/development.db" // 改为子目录

	// 创建目录（如果不存在）
	if err := os.MkdirAll("data", os.ModePerm); err != nil {
		panic("无法创建 data 目录: " + err.Error())
	}

	var err error
	DB, err = gorm.Open(sqlite.Open(dbPath), &gorm.Config{})
	if err != nil {
		panic("failed to connect database: " + err.Error())
	}

	// 自动迁移
	DB.AutoMigrate(&models.User{})
}
