package main

import (
	"fmt"
	"log"
	"sync"
	"time"
)

// 简化的消息队列
type MessageQueue struct {
	topics map[string][]Message
	mutex  sync.RWMutex
}

type Message struct {
	ID      string      `json:"id"`
	Topic   string      `json:"topic"`
	Data    interface{} `json:"data"`
	Created time.Time   `json:"created"`
}

var queue = &MessageQueue{
	topics: make(map[string][]Message),
}

// 发布消息
func (q *MessageQueue) Publish(topic string, data interface{}) {
	q.mutex.Lock()
	defer q.mutex.Unlock()
	
	msg := Message{
		ID:      fmt.Sprintf("msg_%d", time.Now().UnixNano()),
		Topic:   topic,
		Data:    data,
		Created: time.Now(),
	}
	
	q.topics[topic] = append(q.topics[topic], msg)
	log.Printf("Message published to topic '%s': %s", topic, msg.ID)
}

// 订阅消息
func (q *MessageQueue) Subscribe(topic string, handler func(Message)) {
	go func() {
		for {
			q.mutex.Lock()
			messages := q.topics[topic]
			if len(messages) > 0 {
				// 取出第一条消息
				msg := messages[0]
				q.topics[topic] = messages[1:]
				q.mutex.Unlock()
				
				// 处理消息
				handler(msg)
			} else {
				q.mutex.Unlock()
				time.Sleep(100 * time.Millisecond) // 等待新消息
			}
		}
	}()
}

// 图片消息结构
type ImageMessage struct {
	URL       string    `json:"url"`
	UserID    string    `json:"user_id"`
	Timestamp time.Time `json:"timestamp"`
}

// 生产者
func startProducer() {
	topic := "image_process"
	
	for i := 0; i < 5; i++ {
		msg := ImageMessage{
			URL:       fmt.Sprintf("https://example.com/image_%d.jpg", i+1),
			UserID:    fmt.Sprintf("user_%d", i+1),
			Timestamp: time.Now(),
		}
		
		queue.Publish(topic, msg)
		time.Sleep(1 * time.Second)
	}
	
	log.Println("Producer finished")
}

// 消费者
func startConsumer() {
	topic := "image_process"
	
	queue.Subscribe(topic, func(msg Message) {
		var imgMsg ImageMessage
		if data, ok := msg.Data.(ImageMessage); ok {
			imgMsg = data
		} else {
			log.Printf("Invalid message format: %+v", msg.Data)
			return
		}
		
		log.Printf("Processing image: URL=%s, UserID=%s", imgMsg.URL, imgMsg.UserID)
		
		// 模拟图片处理
		time.Sleep(500 * time.Millisecond)
		
		log.Printf("Image processed successfully: %s", imgMsg.URL)
	})
	
	log.Printf("Consumer started, listening to topic: %s", topic)
}

func main() {
	log.Println("Starting simplified message queue example...")
	
	// 启动消费者
	startConsumer()
	
	// 等待一下让消费者准备就绪
	time.Sleep(1 * time.Second)
	
	// 启动生产者
	startProducer()
	
	// 等待处理完成
	time.Sleep(3 * time.Second)
	log.Println("Example completed")
} 