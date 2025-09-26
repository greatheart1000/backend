// routes/auth_routes.go
package routes

import (
	"go-echo/handlers"
	"go-echo/middleware"
	"github.com/labstack/echo/v4"
)

func SetupAuthRoutes(e *echo.Echo) {
	// 公开路由
	e.POST("/register", handlers.Register)
	e.POST("/login", handlers.Login)
	e.POST("/forgot-password", handlers.ForgotPassword)
	e.POST("/reset-password", handlers.ResetPassword)

	// 受保护的路由
	protected := e.Group("/protected")
	protected.Use(middleware.JWTMiddleware())
	protected.GET("/profile", handlers.Profile)
}
