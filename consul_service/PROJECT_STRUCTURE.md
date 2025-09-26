微服务发现项目/
├── README.md                             # 项目总览文档
├── requirements.txt                      # 通用依赖
├── test_api.py                          # API 测试脚本
├── scripts/                             # 旧脚本(兼容性保留)
│   ├── start_consul.sh
│   ├── start_consul.bat
│   ├── start_etcd.sh
│   ├── start_etcd.bat
│   ├── run_services.sh
│   ├── run_services.bat
│   └── run_etcd_services.sh
├── consul_discovery/                    # Consul 服务发现实现
│   ├── README.md                        # Consul 方案说明
│   ├── requirements.txt                 # Consul 专用依赖
│   ├── consul_service.py                # Consul 服务发现核心库
│   ├── config.py                        # 配置文件
│   ├── services/                        # 微服务
│   │   ├── user_service/
│   │   │   └── main.py                  # 用户服务
│   │   └── order_service/
│   │       └── main.py                  # 订单服务
│   ├── client/                          # 客户端示例
│   │   └── main.py                      # 服务发现调用示例
│   └── scripts/                         # 启动脚本
│       ├── start_consul.sh              # 启动 Consul (Linux/macOS)
│       ├── start_consul.bat             # 启动 Consul (Windows)
│       ├── run_services.sh              # 启动所有服务 (Linux/macOS)
│       └── run_services.bat             # 启动所有服务 (Windows)
└── kubernetes_discovery/                # Kubernetes(Etcd) 服务发现实现
    ├── README.md                        # Kubernetes 方案说明
    ├── requirements.txt                 # Etcd 专用依赖
    ├── etcd_service.py                  # Etcd 服务发现核心库
    ├── config.py                        # 配置文件
    ├── services/                        # 微服务
    │   ├── user_service/
    │   │   └── main.py                  # 用户服务
    │   └── order_service/
    │       └── main.py                  # 订单服务
    ├── client/                          # 客户端示例
    │   └── main.py                      # 服务发现调用示例
    ├── scripts/                         # 启动脚本
    │   ├── start_etcd.sh                # 启动 Etcd (Linux/macOS)
    │   ├── start_etcd.bat               # 启动 Etcd (Windows)
    │   └── run_etcd_services.sh         # 启动所有服务
    └── docs/                            # 详细文档
        └── ETCD_SERVICE_DISCOVERY.md    # Etcd 详细实现指南