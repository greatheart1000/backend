package main

import (
    "crypto/rand"
    "encoding/hex"
    "encoding/json"
    "html/template"
    "log"
    mathrand "math/rand"
    "net/http"
    "time"

    "golang.org/x/crypto/bcrypt"
)

var (
    tpl      = template.Must(template.ParseFiles("templates/home_go.html", "templates/login_go.html", "templates/register_go.html"))
    users    = map[string][]byte{}   // username -> bcrypt(password)
    sessions = map[string]string{}   // sessionID -> username
)

const sessionCookieName = "session_id"

// 数据结构定义
type MarketData struct {
    Name      string  `json:"name"`
    Code      string  `json:"code"`
    Price     float64 `json:"price"`
    Change    float64 `json:"change"`
    ChangePct float64 `json:"changePct"`
}

type NewsItem struct {
    ID      int    `json:"id"`
    Title   string `json:"title"`
    Summary string `json:"summary"`
    Time    string `json:"time"`
    IsVIP   bool   `json:"isVIP"`
}

type FuturesData struct {
    Name      string  `json:"name"`
    Code      string  `json:"code"`
    Price     float64 `json:"price"`
    Change    float64 `json:"change"`
    ChangePct float64 `json:"changePct"`
}

type StockData struct {
    Name      string  `json:"name"`
    Code      string  `json:"code"`
    Price     float64 `json:"price"`
    Change    float64 `json:"change"`
    ChangePct float64 `json:"changePct"`
}

type VideoItem struct {
    ID       int    `json:"id"`
    Title    string `json:"title"`
    Thumbnail string `json:"thumbnail"`
    Views    int    `json:"views"`
    Time     string `json:"time"`
}

type VIPContent struct {
    ID    int    `json:"id"`
    Type  string `json:"type"`
    Title string `json:"title"`
    Desc  string `json:"desc"`
}

type MarketCalendar struct {
    ID      int    `json:"id"`
    Event   string `json:"event"`
    Date    string `json:"date"`
    Status  string `json:"status"`
}

// randToken 生成一个随机 session ID
func randToken() string {
    b := make([]byte, 16)
    if _, err := rand.Read(b); err != nil {
        panic(err)
    }
    return hex.EncodeToString(b)
}

// getUserFromSession 从 Cookie 中读取 sessionID，再查 sessions
func getUserFromSession(r *http.Request) (string, bool) {
    c, err := r.Cookie(sessionCookieName)
    if err != nil {
        return "", false
    }
    username, ok := sessions[c.Value]
    return username, ok
}

// 生成模拟市场数据
func generateMarketData() []MarketData {
    return []MarketData{
        {Name: "上证指数", Code: "SH000001", Price: 3245.67 + mathrand.Float64()*100, Change: 1.23, ChangePct: 1.23},
        {Name: "深证成指", Code: "SZ399001", Price: 12456.78 + mathrand.Float64()*200, Change: -0.45, ChangePct: -0.45},
        {Name: "恒生指数", Code: "HSI", Price: 18234.56 + mathrand.Float64()*300, Change: 0.78, ChangePct: 0.78},
        {Name: "道琼斯", Code: "DJI", Price: 34567.89 + mathrand.Float64()*500, Change: 0.92, ChangePct: 0.92},
    }
}

// 生成模拟新闻数据
func generateNewsData() []NewsItem {
    return []NewsItem{
        {
            ID:      1,
            Title:   "央行宣布降准0.25个百分点，释放长期资金约5000亿元",
            Summary: "此举旨在支持实体经济发展，保持流动性合理充裕...",
            Time:    "10分钟前",
            IsVIP:   true,
        },
        {
            ID:      2,
            Title:   "美联储官员暗示可能暂停加息，市场预期转向",
            Summary: "多位美联储官员表示，当前利率水平可能已经足够限制性...",
            Time:    "25分钟前",
            IsVIP:   false,
        },
        {
            ID:      3,
            Title:   "新能源汽车销量再创新高，产业链公司业绩亮眼",
            Summary: "数据显示，新能源汽车渗透率持续提升，相关公司股价表现强劲...",
            Time:    "1小时前",
            IsVIP:   false,
        },
        {
            ID:      4,
            Title:   "A股三大指数集体收涨，科技股领涨",
            Summary: "今日A股市场表现活跃，科技板块涨幅居前...",
            Time:    "2小时前",
            IsVIP:   false,
        },
    }
}

// 生成模拟期货数据
func generateFuturesData() []FuturesData {
    return []FuturesData{
        {Name: "螺纹钢", Code: "RB2405", Price: 3456 + mathrand.Float64()*100, Change: 2.1, ChangePct: 2.1},
        {Name: "铁矿石", Code: "I2405", Price: 789 + mathrand.Float64()*50, Change: -1.2, ChangePct: -1.2},
        {Name: "原油", Code: "SC2405", Price: 567 + mathrand.Float64()*30, Change: 0.8, ChangePct: 0.8},
        {Name: "黄金", Code: "AU2406", Price: 2345 + mathrand.Float64()*100, Change: 1.5, ChangePct: 1.5},
    }
}

// 生成模拟股票数据
func generateStockData() []StockData {
    return []StockData{
        {Name: "贵州茅台", Code: "600519", Price: 1856.00 + mathrand.Float64()*50, Change: 2.3, ChangePct: 2.3},
        {Name: "宁德时代", Code: "300750", Price: 234.50 + mathrand.Float64()*20, Change: -1.1, ChangePct: -1.1},
        {Name: "比亚迪", Code: "002594", Price: 198.80 + mathrand.Float64()*30, Change: 3.2, ChangePct: 3.2},
        {Name: "腾讯控股", Code: "00700", Price: 345.60 + mathrand.Float64()*40, Change: 1.8, ChangePct: 1.8},
    }
}

// 生成模拟视频数据
func generateVideoData() []VideoItem {
    return []VideoItem{
        {
            ID:        1,
            Title:     "今日市场分析：A股震荡上行，关注这些板块",
            Thumbnail: "https://via.placeholder.com/300x200/1e3a8a/ffffff?text=市场分析",
            Views:     23000,
            Time:      "15分钟前",
        },
        {
            ID:        2,
            Title:     "投资策略分享：如何把握市场节奏",
            Thumbnail: "https://via.placeholder.com/300x200/f59e0b/ffffff?text=投资策略",
            Views:     18000,
            Time:      "1小时前",
        },
        {
            ID:        3,
            Title:     "期货交易技巧：风险控制要点",
            Thumbnail: "https://via.placeholder.com/300x200/10b981/ffffff?text=期货技巧",
            Views:     15000,
            Time:      "2小时前",
        },
    }
}

// 生成模拟VIP内容
func generateVIPContent() []VIPContent {
    return []VIPContent{
        {
            ID:    1,
            Type:  "report",
            Title: "《2024年投资策略报告》",
            Desc:  "独家深度分析，把握投资机会",
        },
        {
            ID:    2,
            Type:  "alert",
            Title: "实时预警",
            Desc:  "重要市场信号提醒",
        },
        {
            ID:    3,
            Type:  "analysis",
            Title: "《行业深度研究报告》",
            Desc:  "专业分析师团队出品",
        },
    }
}

// 生成模拟市场日历
func generateMarketCalendar() []MarketCalendar {
    return []MarketCalendar{
        {ID: 1, Event: "美联储议息会议", Date: "今日", Status: "primary"},
        {ID: 2, Event: "中国CPI数据公布", Date: "明日", Status: "secondary"},
        {ID: 3, Event: "欧央行利率决议", Date: "本周四", Status: "info"},
        {ID: 4, Event: "美国非农数据", Date: "下周五", Status: "warning"},
    }
}

// API接口处理函数
func apiMarketData(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateMarketData()
    json.NewEncoder(w).Encode(data)
}

func apiNews(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateNewsData()
    json.NewEncoder(w).Encode(data)
}

func apiFutures(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateFuturesData()
    json.NewEncoder(w).Encode(data)
}

func apiStocks(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateStockData()
    json.NewEncoder(w).Encode(data)
}

func apiVideos(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateVideoData()
    json.NewEncoder(w).Encode(data)
}

func apiVIPContent(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateVIPContent()
    json.NewEncoder(w).Encode(data)
}

func apiMarketCalendar(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    data := generateMarketCalendar()
    json.NewEncoder(w).Encode(data)
}

func registerGet(w http.ResponseWriter, r *http.Request) {
    tpl.ExecuteTemplate(w, "register_go.html", nil)
}

func registerPost(w http.ResponseWriter, r *http.Request) {
    username := r.FormValue("username")
    password := r.FormValue("password")
    if username == "" || password == "" {
        http.Error(w, "用户名和密码不能为空", http.StatusBadRequest)
        return
    }
    if _, exists := users[username]; exists {
        http.Error(w, "用户已存在", http.StatusBadRequest)
        return
    }
    hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        http.Error(w, "服务器错误", http.StatusInternalServerError)
        return
    }
    users[username] = hash
    http.Redirect(w, r, "/login", http.StatusSeeOther)
}

func loginGet(w http.ResponseWriter, r *http.Request) {
    tpl.ExecuteTemplate(w, "login_go.html", nil)
}

func loginPost(w http.ResponseWriter, r *http.Request) {
    username := r.FormValue("username")
    password := r.FormValue("password")
    hash, exists := users[username]
    if !exists || bcrypt.CompareHashAndPassword(hash, []byte(password)) != nil {
        http.Error(w, "用户名或密码错误", http.StatusUnauthorized)
        return
    }
    // 创建新 session
    sid := randToken()
    sessions[sid] = username
    http.SetCookie(w, &http.Cookie{
        Name:    sessionCookieName,
        Value:   sid,
        Path:    "/",
        Expires: time.Now().Add(24 * time.Hour),
    })
    http.Redirect(w, r, "/home", http.StatusSeeOther)
}

func home(w http.ResponseWriter, r *http.Request) {
    user, ok := getUserFromSession(r)
    if !ok {
        http.Redirect(w, r, "/login", http.StatusSeeOther)
        return
    }
    tpl.ExecuteTemplate(w, "home_go.html", user)
}

func logout(w http.ResponseWriter, r *http.Request) {
    c, err := r.Cookie(sessionCookieName)
    if err == nil {
        delete(sessions, c.Value)
        // 删除 cookie
        http.SetCookie(w, &http.Cookie{
            Name:    sessionCookieName,
            Value:   "",
            Path:    "/",
            Expires: time.Unix(0, 0),
        })
    }
    http.Redirect(w, r, "/login", http.StatusSeeOther)
}

func main() {
    // 初始化随机数种子
    mathrand.Seed(time.Now().UnixNano())
    
    mux := http.NewServeMux()
    
    // 页面路由
    mux.HandleFunc("/register", func(w http.ResponseWriter, r *http.Request) {
        if r.Method == http.MethodPost {
            registerPost(w, r)
        } else {
            registerGet(w, r)
        }
    })
    mux.HandleFunc("/login", func(w http.ResponseWriter, r *http.Request) {
        if r.Method == http.MethodPost {
            loginPost(w, r)
        } else {
            loginGet(w, r)
        }
    })
    mux.HandleFunc("/home", home)
    mux.HandleFunc("/logout", logout)
    
    // API接口路由
    mux.HandleFunc("/api/market-data", apiMarketData)
    mux.HandleFunc("/api/news", apiNews)
    mux.HandleFunc("/api/futures", apiFutures)
    mux.HandleFunc("/api/stocks", apiStocks)
    mux.HandleFunc("/api/videos", apiVideos)
    mux.HandleFunc("/api/vip-content", apiVIPContent)
    mux.HandleFunc("/api/market-calendar", apiMarketCalendar)

    log.Println("启动于 http://localhost:8080 …")
    log.Println("API接口:")
    log.Println("  GET /api/market-data     - 市场数据")
    log.Println("  GET /api/news           - 新闻资讯")
    log.Println("  GET /api/futures        - 期货行情")
    log.Println("  GET /api/stocks         - 股票数据")
    log.Println("  GET /api/videos         - 视频内容")
    log.Println("  GET /api/vip-content    - VIP内容")
    log.Println("  GET /api/market-calendar - 市场日历")
    log.Fatal(http.ListenAndServe(":8080", mux))
}