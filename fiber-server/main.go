package main

import (
	"database/sql"
	"log"

	"github.com/gofiber/fiber/v2"
	_ "github.com/go-sql-driver/mysql"
)

// User 结构体用于映射数据库表和 JSON 请求
type User struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
	Age  int    `json:"age"`
	Role string `json:"role"` // 新增的权限字段
}

// 全局变量来存储数据库连接
var db *sql.DB

func main() {
	var err error
	// 替换为你的数据库连接信息，格式："[用户名]:[密码]@tcp([主机名]:[端口])/[数据库名]"
	// 推荐连接到你自己创建的数据库，如 "testdb"
	db, err = sql.Open("mysql", "root:123456@tcp(127.0.0.1:3306)/mysql")
	if err != nil {
		log.Fatalf("无法连接到数据库: %v", err)
	}
	defer db.Close() // 确保程序退出时关闭连接

	// 检查数据库连接是否成功
	err = db.Ping()
	if err != nil {
		log.Fatalf("无法 Ping 数据库: %v", err)
	}
	log.Println("成功连接到 MySQL 数据库！")

	app := fiber.New()

	// --- 基础 API 接口 ---
	// GET /
	app.Get("/", func(c *fiber.Ctx) error {
		return c.SendString("Hello, World!")
	})

	// GET /api/users/:id
	app.Get("/api/users/:id", func(c *fiber.Ctx) error {
		id := c.Params("id")
		return c.SendString("User ID: " + id)
	})

	// POST /api/users
	app.Post("/api/users", func(c *fiber.Ctx) error {
		user := new(User)
		if err := c.BodyParser(user); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "Cannot parse JSON",
			})
		}
		log.Printf("Received user: %+v", user)
		return c.Status(fiber.StatusOK).JSON(fiber.Map{
			"message": "User received successfully",
			"user":    user,
		})
	})


	// --- 数据库操作及权限控制接口 ---

	// POST /users: 新增一个用户
	// 接收 JSON 数据，将其插入数据库，角色默认设置为 'user'
	app.Post("/users", func(c *fiber.Ctx) error {
		user := new(User)
		if err := c.BodyParser(user); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{"error": "无法解析 JSON"})
		}
		
		user.Role = "user" // 新用户默认角色为 'user'

		// 插入数据到数据库
		result, err := db.Exec("INSERT INTO users (name, age, role) VALUES (?, ?, ?)", user.Name, user.Age, user.Role)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "无法插入数据"})
		}

		id, _ := result.LastInsertId()
		user.ID = int(id)

		return c.Status(fiber.StatusCreated).JSON(user)
	})

	// GET /users: 查询所有用户
	// 仅限管理员（role: 'admin'）访问
	app.Get("/users", func(c *fiber.Ctx) error {
		// 模拟从请求头中获取用户角色
		// 实际项目中，这通常来自 JWT token 或 session
		userRole := c.Get("X-User-Role")

		// 权限控制：如果角色不是 'admin'，则拒绝访问
		if userRole != "admin" {
			return c.Status(fiber.StatusForbidden).JSON(fiber.Map{"error": "您没有权限访问此资源"})
		}

		// 执行数据库查询
		rows, err := db.Query("SELECT id, name, age, role FROM users")
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "无法查询数据"})
		}
		defer rows.Close()

		var users []User
		for rows.Next() {
			var user User
			if err := rows.Scan(&user.ID, &user.Name, &user.Age, &user.Role); err != nil {
				return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "无法扫描行"})
			}
			users = append(users, user)
		}

		return c.Status(fiber.StatusOK).JSON(users)
	})

	// 启动服务器，监听 3000 端口
	log.Fatal(app.Listen(":3000"))
}
