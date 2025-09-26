package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"
	"time"
)

// 简化的服务注册中心
type ServiceRegistry struct {
	services map[string][]ServiceInstance
	mutex    sync.RWMutex
}

type ServiceInstance struct {
	ID      string `json:"id"`
	Name    string `json:"name"`
	Address string `json:"address"`
	Port    int    `json:"port"`
	Healthy bool   `json:"healthy"`
}

var registry = &ServiceRegistry{
	services: make(map[string][]ServiceInstance),
}

// 注册服务
func (r *ServiceRegistry) Register(service ServiceInstance) {
	r.mutex.Lock()
	defer r.mutex.Unlock()
	
	r.services[service.Name] = append(r.services[service.Name], service)
	log.Printf("Service registered: %s at %s:%d", service.Name, service.Address, service.Port)
}

// 发现服务
func (r *ServiceRegistry) Discover(serviceName string) []ServiceInstance {
	r.mutex.RLock()
	defer r.mutex.RUnlock()
	
	instances := r.services[serviceName]
	var healthyInstances []ServiceInstance
	for _, instance := range instances {
		if instance.Healthy {
			healthyInstances = append(healthyInstances, instance)
		}
	}
	return healthyInstances
}

// Order 服务
func startOrderService() {
	service := ServiceInstance{
		ID:      "order-service-1",
		Name:    "order-service",
		Address: "127.0.0.1",
		Port:    8081,
		Healthy: true,
	}
	
	registry.Register(service)
	
	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})
	
	http.HandleFunc("/create", func(w http.ResponseWriter, r *http.Request) {
		orderID := fmt.Sprintf("order_%d", time.Now().Unix())
		response := map[string]interface{}{
			"order_id":  orderID,
			"status":    "created",
			"timestamp": time.Now().Format("2006-01-02 15:04:05"),
		}
		
		json.NewEncoder(w).Encode(response)
		log.Printf("Order created: %s", orderID)
	})
	
	log.Printf("Order service starting on :%d", service.Port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", service.Port), nil))
}

// User 客户端
func startUserClient() {
	time.Sleep(2 * time.Second) // 等待服务启动
	
	for i := 0; i < 3; i++ {
		instances := registry.Discover("order-service")
		if len(instances) == 0 {
			log.Println("No order service instances available")
			time.Sleep(1 * time.Second)
			continue
		}
		
		// 选择第一个实例
		instance := instances[0]
		url := fmt.Sprintf("http://%s:%d/create", instance.Address, instance.Port)
		
		resp, err := http.Get(url)
		if err != nil {
			log.Printf("Error calling order service: %v", err)
			continue
		}
		defer resp.Body.Close()
		
		var result map[string]interface{}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			log.Printf("Error decoding response: %v", err)
			continue
		}
		
		log.Printf("Order service response: %+v", result)
		time.Sleep(1 * time.Second)
	}
}

func main() {
	log.Println("Starting simplified service discovery example...")
	
	// 启动 Order 服务
	go startOrderService()
	
	// 启动 User 客户端
	startUserClient()
} 