package main

import (
	"fmt"
	"sync"
)

func sq(in chan int) <-chan int {
	out := make(chan int)
	go func() {
		for i := range in {
			out <- i * i
		}
		close(out)
	}()
	return out
}

func gen(nums ...int) <-chan int {
	out := make(chan int, len(nums)) //带缓冲通道
	for _, n := range nums {
		out <- n
	}
	close(out)
	return out
}

func mission(done <-chan struct{}, in <-chan int) <-chan int {
	out := make(chan int) //创建一个无缓冲通道
	go func() {
		defer close(out) //确保通道在函数结束时关闭
		for n := range in {
			select {
			case out <- n * n: //将平方值发送到输出通道
			case <-done:
				return
			}
		}
	}()
	return out
}

func merge(cs ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	out := make(chan int)

	// 为每个输入通道启动一个 goroutine
	output := func(c <-chan int) {
		for n := range c {
			out <- n // 直接发送到输出通道
		}
		wg.Done() // 任务完成，减少计数器
	}

	// 为每个输入通道添加任务
	wg.Add(len(cs))
	for _, c := range cs {
		go output(c)
	}

	// 等待所有 goroutine 完成并关闭输出通道
	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

func main() {
	in := make(chan int, 10)
	go func() {
		for i := 0; i < 10; i++ {
			in <- i
		}
		close(in) //显式关闭通道
	}()
	out := sq(in)
	for result := range out {
		fmt.Println(result)
	}
	fmt.Println("Done")

	ch := gen(1, 2, 3, 4, 5)
	for num := range ch {
		fmt.Println(num)
	}
	fmt.Println("ch111111111111")
	in = make(chan int, 10)
	go func() {
		for i := 0; i < 10; i++ {
			in <- i
		}
		close(in)
	}()
	done := make(chan struct{})

	defer close(done) //确保在主函数结束时关闭done通道
	out = mission(done, in)
	for result := range out {
		fmt.Println(result)
	}

	ch1 := gen(1, 2, 3)
	ch2 := gen(4, 5, 6)
	out1 := merge(ch1, ch2)

	// 接收并打印输出
	for result := range out1 {
		fmt.Println(result)
	}

}
