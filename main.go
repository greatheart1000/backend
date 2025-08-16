package main

import (
	"fmt"
	"go_learn/interfacepkg"
	"go_learn/reflectpkg"
)

func sq(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		for n := range in {
			out <- n * n
		}
		close(out)
	}()
	return out
}

func main() {
	// 调用排序功能
	people := []interfacepkg.Person{
		{Name: "Bob", Age: 31},
		{Name: "John", Age: 42},
		{Name: "Michael", Age: 17},
		{Name: "Jenny", Age: 26},
	}
	fmt.Println("Original people:", people)
	interfacepkg.Sort(interfacepkg.ByAge(people))
	fmt.Println("Sorted by age:", people)

	// 调用反射功能
	var x int = 42
	reflectpkg.PrintTypeAndValue(x)

	p := interfacepkg.Person{Name: "Alice", Age: 25}
	reflectpkg.PrintTypeAndValue(p)

	var p2 = interfacepkg.Person{Name: "Bob", Age: 30}
	fmt.Println("Before modification:", p2)
	reflectpkg.ModifyValue(&p2)
	fmt.Println("After modification:", p2)
}
