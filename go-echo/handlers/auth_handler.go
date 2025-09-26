// handlers/auth_handler.go
package handlers

import (
	"go-echo/config"
	"go-echo/models"
	"go-echo/utils"
	"net/http"

	"github.com/go-playground/validator/v10"
	"github.com/labstack/echo/v4"
)

var validate = validator.New()

// Register 用户注册
func Register(c echo.Context) error {
	type RegisterRequest struct {
		Username string `json:"username"`
		Email    string `json:"email"`
		Password string `json:"password"`
	}
	
	req := &RegisterRequest{}
	if err := c.Bind(req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "请求格式无效"})
	}

	// 验证用户名
	if err := models.ValidateUsername(req.Username); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}
	
	// 验证邮箱格式
	if err := models.ValidateEmail(req.Email); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}
	
	// 验证密码强度
	if err := models.ValidatePassword(req.Password); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}

	// 检查邮箱是否已存在
	var existingUser models.User
	if err := config.DB.Where("email = ?", req.Email).First(&existingUser).Error; err == nil {
		return c.JSON(http.StatusConflict, map[string]string{"error": "该邮箱已被注册"})
	}
	
	// 检查用户名是否已存在
	if err := config.DB.Where("username = ?", req.Username).First(&existingUser).Error; err == nil {
		return c.JSON(http.StatusConflict, map[string]string{"error": "该用户名已被使用"})
	}

	// 创建新用户
	u := &models.User{
		Username: req.Username,
		Email:    req.Email,
	}
	
	// 加密密码
	if err := u.SetPassword(req.Password); err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "密码加密失败"})
	}

	// 保存用户
	if err := config.DB.Create(u).Error; err != nil {
		c.Logger().Errorf("Failed to create user: %v", err)
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "用户创建失败"})
	}

	// 返回成功响应
	return c.JSON(http.StatusCreated, map[string]interface{}{
		"message": "用户注册成功",
		"user": map[string]interface{}{
			"id":       u.ID,
			"username": u.Username,
			"email":    u.Email,
		},
	})
}

// Login 用户登录
func Login(c echo.Context) error {
	type LoginRequest struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}
	
	req := &LoginRequest{}
	if err := c.Bind(req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "请求格式无效"})
	}
	
	// 验证邮箱格式
	if err := models.ValidateEmail(req.Email); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}
	
	// 验证密码不能为空
	if req.Password == "" {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "密码不能为空"})
	}

	// 查找用户
	var user models.User
	if err := config.DB.Where("email = ?", req.Email).First(&user).Error; err != nil {
		c.Logger().Warnf("Login failed: user not found for email=%s", req.Email)
		return c.JSON(http.StatusUnauthorized, map[string]string{"error": "用户不存在或密码错误"})
	}

	// 验证密码
	if !user.CheckPassword(req.Password) {
		c.Logger().Warnf("Login failed: wrong password for user=%s (ID=%d)", user.Username, user.ID)
		return c.JSON(http.StatusUnauthorized, map[string]string{"error": "用户不存在或密码错误"})
	}

	// 生成 JWT Token
	token, err := utils.GenerateToken(&user)
	if err != nil {
		c.Logger().Errorf("Token generation failed for user=%d: %v", user.ID, err)
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "令牌生成失败"})
	}

	// 登录成功
	c.Logger().Infof("User logged in successfully: ID=%d, Username=%s", user.ID, user.Username)

	return c.JSON(http.StatusOK, map[string]interface{}{
		"message": "登录成功",
		"token":   token,
		"user": map[string]interface{}{
			"id":       user.ID,
			"username": user.Username,
			"email":    user.Email,
		},
	})
}

// Profile 获取当前用户信息
func Profile(c echo.Context) error {
	// 从 JWT 中获取 userID
	userID, ok := c.Get("userID").(uint)
	if !ok {
		return c.JSON(http.StatusUnauthorized, map[string]string{"error": "Invalid user ID in token"})
	}

	var user models.User
	if err := config.DB.Select("id, username, email").First(&user, userID).Error; err != nil {
		c.Logger().Warnf("Profile not found for userID=%d", userID)
		return c.JSON(http.StatusNotFound, map[string]string{"error": "User not found"})
	}

	return c.JSON(http.StatusOK, user)
}

// ForgotPassword 忘记密码 - 发送重置令牌
func ForgotPassword(c echo.Context) error {
	type ForgotPasswordRequest struct {
		Email string `json:"email"`
	}
	
	req := &ForgotPasswordRequest{}
	if err := c.Bind(req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "请求格式无效"})
	}
	
	// 验证邮箱格式
	if err := models.ValidateEmail(req.Email); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}
	
	// 查找用户
	var user models.User
	if err := config.DB.Where("email = ?", req.Email).First(&user).Error; err != nil {
		// 为了安全，即使用户不存在也返回成功消息，不泄露用户信息
		c.Logger().Warnf("Forgot password attempt for non-existent email: %s", req.Email)
		return c.JSON(http.StatusOK, map[string]string{"message": "如果该邮箱已注册，您将收到密码重置邮件"})
	}
	
	// 生成重置令牌
	if err := user.GenerateResetToken(); err != nil {
		c.Logger().Errorf("Failed to generate reset token for user %d: %v", user.ID, err)
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "重置令牌生成失败"})
	}
	
	// 保存重置令牌到数据库
	if err := config.DB.Save(&user).Error; err != nil {
		c.Logger().Errorf("Failed to save reset token for user %d: %v", user.ID, err)
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "保存重置令牌失败"})
	}
	
	// 在实际应用中，这里应该发送邮件给用户
	// 现在我们暂时在日志中显示令牌（仅用于开发测试）
	c.Logger().Infof("Password reset token for %s: %s (expires: %v)", user.Email, user.ResetToken, user.ResetTokenExpiry)
	
	// 开发模式下返回令牌（生产环境应该删除这部分）
	return c.JSON(http.StatusOK, map[string]interface{}{
		"message": "如果该邮箱已注册，您将收到密码重置邮件",
		"reset_token": user.ResetToken, // 仅用于开发测试
	})
}

// ResetPassword 重置密码
func ResetPassword(c echo.Context) error {
	type ResetPasswordRequest struct {
		Token       string `json:"token"`
		NewPassword string `json:"new_password"`
	}
	
	req := &ResetPasswordRequest{}
	if err := c.Bind(req); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "请求格式无效"})
	}
	
	// 验证令牌不能为空
	if req.Token == "" {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "重置令牌不能为空"})
	}
	
	// 验证新密码
	if err := models.ValidatePassword(req.NewPassword); err != nil {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": err.Error()})
	}
	
	// 查找拥有该令牌的用户
	var user models.User
	if err := config.DB.Where("reset_token = ?", req.Token).First(&user).Error; err != nil {
		c.Logger().Warnf("Invalid reset token attempted: %s", req.Token)
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "无效的重置令牌"})
	}
	
	// 验证令牌是否有效且未过期
	if !user.ValidateResetToken(req.Token) {
		c.Logger().Warnf("Expired or invalid reset token for user %d", user.ID)
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "重置令牌已过期或无效"})
	}
	
	// 设置新密码
	if err := user.SetPassword(req.NewPassword); err != nil {
		c.Logger().Errorf("Failed to set new password for user %d: %v", user.ID, err)
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "密码设置失败"})
	}
	
	// 清除重置令牌
	user.ClearResetToken()
	
	// 保存更改
	if err := config.DB.Save(&user).Error; err != nil {
		c.Logger().Errorf("Failed to save password reset for user %d: %v", user.ID, err)
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": "保存密码失败"})
	}
	
	c.Logger().Infof("Password reset successfully for user %d", user.ID)
	
	return c.JSON(http.StatusOK, map[string]string{"message": "密码重置成功"})
}
