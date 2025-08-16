package main

import (
	"fmt"
	"time"
)

func count(a int, b int, exitChan chan bool) {
	c := a + b
	fmt.Printf("The Result of %d + %d = %d\n", a, b, c)
	time.Sleep(time.Second * 2)
	exitChan <- true
}

func foo() *int {
	var a int
	return &a
}

func foo1() int {
	x := new(int) //初始化 但这个值一般是0
	*x = 10
	return *x
}

func main() {

	p := foo()
	fmt.Printf("foo 返回的指针: %p，解引用后的值: %d\n", p, *p)

	p1 := foo1()
	fmt.Printf("foo1 返回的值: %d\n", p1)

	exitChan := make(chan bool, 10) //声明并分配管道内存
	for i := 0; i < 10; i++ {
		go count(i, i+1, exitChan)
	}
	for j := 0; j < 10; j++ {
		<-exitChan //取信号数据，如果取不到则会阻塞
	}
	close(exitChan) // 关闭管道
}

// func count(a int, b int) int {
// 	sum := a + b
// 	fmt.Println("Sum:", sum)
// 	return sum
// }

// func main() {
// 	// Create a channel to communicate between goroutines
// 	for i := 0; i < 10; i++ {
// 		go count(i, i+1) //启动10个goroutine 来计算

// 	}
// 	time.Sleep(3 * time.Second) // Sleep to allow goroutine to finish
// }
