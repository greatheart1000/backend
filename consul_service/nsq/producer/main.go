package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/nsqio/go-nsq"
)

type ImageMessage struct {
	URL       string    `json:"url"`
	Timestamp time.Time `json:"timestamp"`
	UserID    string    `json:"user_id"`
}

func main() {
	cfg := nsq.NewConfig()
	producer, err := nsq.NewProducer("127.0.0.1:4150", cfg) // nsqd 的 TCP 地址
	if err != nil {
		log.Fatalf("failed to create producer: %v", err)
	}
	defer producer.Stop()

	topic := "image_process"

	// 模拟用户上传图片
	for i := 0; i < 5; i++ {
		msg := ImageMessage{
			URL:       fmt.Sprintf("https://example.com/image_%d.jpg", i+1),
			Timestamp: time.Now(),
			UserID:    fmt.Sprintf("user_%d", i+1),
		}

		// 序列化消息
		msgBytes, err := json.Marshal(msg)
		if err != nil {
			log.Printf("marshal message err: %v", err)
			continue
		}

		// 发布消息
		if err := producer.Publish(topic, msgBytes); err != nil {
			log.Printf("publish err: %v", err)
		} else {
			log.Printf("published message: %s", string(msgBytes))
		}
		
		time.Sleep(1 * time.Second)
	}

	log.Println("Producer finished")
} 