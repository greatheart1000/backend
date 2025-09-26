package main

import (
	"encoding/json"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nsqio/go-nsq"
)

type ImageMessage struct {
	URL       string    `json:"url"`
	Timestamp time.Time `json:"timestamp"`
	UserID    string    `json:"user_id"`
}

type ImageHandler struct{}

func (h *ImageHandler) HandleMessage(m *nsq.Message) error {
	var msg ImageMessage
	if err := json.Unmarshal(m.Body, &msg); err != nil {
		log.Printf("unmarshal message err: %v", err)
		return err
	}

	log.Printf("Processing image: URL=%s, UserID=%s, Timestamp=%s", 
		msg.URL, msg.UserID, msg.Timestamp.Format("2006-01-02 15:04:05"))

	// 模拟图片处理（生成缩略图、压缩等）
	time.Sleep(500 * time.Millisecond)
	
	log.Printf("Image processed successfully: %s", msg.URL)
	return nil
}

func main() {
	cfg := nsq.NewConfig()
	consumer, err := nsq.NewConsumer("image_process", "image_processor_channel", cfg)
	if err != nil {
		log.Fatalf("create consumer err: %v", err)
	}
	
	consumer.AddHandler(&ImageHandler{})

	// 通过 nsqlookupd 自动发现 nsqd 节点
	if err := consumer.ConnectToNSQLookupd("127.0.0.1:4161"); err != nil {
		log.Fatalf("connect to nsqlookupd err: %v", err)
	}

	log.Println("Image processor consumer started. Waiting for messages...")

	// 优雅退出
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
	<-sig

	log.Println("Shutting down consumer...")
	consumer.Stop()
	<-consumer.StopChan
	log.Println("Consumer stopped")
} 