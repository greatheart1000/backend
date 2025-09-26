package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	consulapi "github.com/hashicorp/consul/api"
)

func main() {
	addr := "127.0.0.1"
	port := 8081
	serviceID := "order-service-1"
	serviceName := "order-service"

	// 启动简单 HTTP 服务
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
		log.Printf("Health check request from %s", r.RemoteAddr)
	})

	http.HandleFunc("/create", func(w http.ResponseWriter, r *http.Request) {
		orderID := fmt.Sprintf("order_%d", time.Now().Unix())
		response := fmt.Sprintf(`{"order_id": "%s", "status": "created", "timestamp": "%s"}`, 
			orderID, time.Now().Format("2006-01-02 15:04:05"))
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(response))
		log.Printf("Order created: %s", orderID)
	})

	http.HandleFunc("/list", func(w http.ResponseWriter, r *http.Request) {
		response := `{"orders": [{"id": "order_1", "status": "pending"}, {"id": "order_2", "status": "completed"}]}`
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(response))
		log.Printf("Order list requested")
	})

	// 注册到 Consul
	cfg := consulapi.DefaultConfig()
	if consulAddr := os.Getenv("CONSUL_HTTP_ADDR"); consulAddr != "" {
		cfg.Address = consulAddr
	}
	client, err := consulapi.NewClient(cfg)
	if err != nil {
		log.Fatalf("consul client err: %v", err)
	}

	reg := &consulapi.AgentServiceRegistration{
		ID:      serviceID,
		Name:    serviceName,
		Address: addr,
		Port:    port,
		Tags:    []string{"order", "http"},
		Check: &consulapi.AgentServiceCheck{
			HTTP:     fmt.Sprintf("http://%s:%d/health", addr, port),
			Interval: "10s",
			Timeout:  "3s",
		},
	}
	
	if err := client.Agent().ServiceRegister(reg); err != nil {
		log.Fatalf("register service fail: %v", err)
	}
	log.Printf("registered service %s at %s:%d", serviceName, addr, port)

	// 优雅关闭
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Printf("Starting order service on :%d", port)
		if err := http.ListenAndServe(fmt.Sprintf(":%d", port), nil); err != nil {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	<-sig
	log.Println("Shutting down order service...")
	
	// 注销服务
	if err := client.Agent().ServiceDeregister(serviceID); err != nil {
		log.Printf("deregister service error: %v", err)
	} else {
		log.Println("Service deregistered from Consul")
	}
} 