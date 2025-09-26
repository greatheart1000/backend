package main

import (
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"time"

	consulapi "github.com/hashicorp/consul/api"
)

func main() {
	// 创建 Consul 客户端
	cfg := consulapi.DefaultConfig()
	client, err := consulapi.NewClient(cfg)
	if err != nil {
		log.Fatalf("consul client err: %v", err)
	}

	// 模拟多次调用
	for i := 0; i < 5; i++ {
		callOrderService(client)
		time.Sleep(2 * time.Second)
	}
}

func callOrderService(client *consulapi.Client) {
	// 查询可用的 order-service 实例
	services, _, err := client.Health().Service("order-service", "", true, nil)
	if err != nil {
		log.Printf("service query err: %v", err)
		return
	}
	
	if len(services) == 0 {
		log.Printf("no order-service instances available")
		return
	}

	// 简单的负载选择：随机选择一个实例
	rand.Seed(time.Now().UnixNano())
	selectedIndex := rand.Intn(len(services))
	inst := services[selectedIndex].Service
	
	log.Printf("Selected order service instance: %s:%d", inst.Address, inst.Port)

	// 发起请求 - 创建订单
	url := fmt.Sprintf("http://%s:%d/create", inst.Address, inst.Port)
	clientHTTP := &http.Client{Timeout: 5 * time.Second}
	
	resp, err := clientHTTP.Get(url)
	if err != nil {
		log.Printf("call order service err: %v", err)
		return
	}
	defer resp.Body.Close()
	
	body, _ := io.ReadAll(resp.Body)
	log.Printf("Order service response: %s", string(body))

	// 发起请求 - 获取订单列表
	url = fmt.Sprintf("http://%s:%d/list", inst.Address, inst.Port)
	resp, err = clientHTTP.Get(url)
	if err != nil {
		log.Printf("call order service list err: %v", err)
		return
	}
	defer resp.Body.Close()
	
	body, _ = io.ReadAll(resp.Body)
	log.Printf("Order list response: %s", string(body))
} 