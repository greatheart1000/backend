#!/bin/bash

echo "Starting all services..."

# 启动 Order 服务
echo "Starting Order Service..."
cd order_service
go run main.go &
ORDER_PID=$!
cd ..

# 等待 Order 服务启动
sleep 3

# 启动 User 客户端
echo "Starting User Client..."
cd user_client
go run main.go &
USER_PID=$!
cd ..

echo "All services started!"
echo "Press Ctrl+C to stop all services"

# 等待信号
trap "echo 'Stopping all services...'; kill $ORDER_PID $USER_PID; exit" INT TERM
wait 