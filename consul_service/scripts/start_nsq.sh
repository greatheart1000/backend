#!/bin/bash

echo "Starting NSQ components..."

# 启动 nsqlookupd
echo "Starting nsqlookupd..."
nsqlookupd &
NSQLOOKUPD_PID=$!

# 等待 nsqlookupd 启动
sleep 2

# 启动 nsqd
echo "Starting nsqd..."
nsqd --lookupd-tcp-address=127.0.0.1:4161 &
NSQD_PID=$!

echo "NSQ started successfully!"
echo "NSQ Admin UI: http://localhost:4171"
echo "Press Ctrl+C to stop NSQ"

# 等待信号
trap "echo 'Stopping NSQ...'; kill $NSQD_PID $NSQLOOKUPD_PID; exit" INT TERM
wait 