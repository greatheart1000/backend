package interfacepkg

import "fmt"

// Person 结构体
type Person struct {
	Name string
	Age  int
}

func (p Person) String() string {
	return fmt.Sprintf("%s: %d", p.Name, p.Age)
}

// Interface 定义排序接口
type Interface interface {
	Len() int
	Less(i, j int) bool
	Swap(i, j int)
}

// Sort 函数：实现排序逻辑
func Sort(data Interface) {
	n := data.Len()
	maxDepth := 0
	for i := n; i > 0; i >>= 1 {
		maxDepth++
	}
	maxDepth *= 2
	quickSort(data, 0, n, maxDepth)
}

// quickSort 函数：快速排序实现
func quickSort(data Interface, a, b, maxDepth int) {
	if b-a < 12 {
		insertionSort(data, a, b)
		return
	}
	if maxDepth == 0 {
		heapSort(data, a, b)
		return
	}

	maxDepth--
	pivot := doPivot(data, a, b)
	quickSort(data, a, pivot, maxDepth)
	quickSort(data, pivot+1, b, maxDepth)
}

// insertionSort 函数：插入排序
func insertionSort(data Interface, a, b int) {
	for i := a + 1; i < b; i++ {
		for j := i; j > a && data.Less(j, j-1); j-- {
			data.Swap(j, j-1)
		}
	}
}

// heapSort 函数：堆排序
func heapSort(data Interface, a, b int) {
	for i := (b - a) / 2; i >= 0; i-- {
		siftDown(data, i, b-a, a)
	}
	for i := b - a - 1; i >= 0; i-- {
		data.Swap(a, a+i)
		siftDown(data, 0, i, a)
	}
}

// siftDown 函数：下沉操作
func siftDown(data Interface, lo, hi, first int) {
	root := lo
	for {
		child := 2*root + 1
		if child >= hi {
			break
		}
		if child+1 < hi && data.Less(first+child, first+child+1) {
			child++
		}
		if !data.Less(first+root, first+child) {
			return
		}
		data.Swap(first+root, first+child)
		root = child
	}
}

// doPivot 函数：选择枢轴并划分
func doPivot(data Interface, lo, hi int) int {
	mid := (lo + hi) / 2
	if data.Less(hi-1, lo) {
		data.Swap(hi-1, lo)
	}
	if data.Less(mid, lo) {
		data.Swap(mid, lo)
	}
	if data.Less(hi-1, mid) {
		data.Swap(hi-1, mid)
	}
	data.Swap(mid, hi-2)
	pivot := hi - 2

	i := lo
	j := hi - 2
	for {
		for {
			i++
			if !data.Less(i, pivot) {
				break
			}
		}
		for {
			j--
			if !data.Less(pivot, j) {
				break
			}
		}
		if i >= j {
			break
		}
		data.Swap(i, j)
	}
	data.Swap(i, pivot)
	return i
}

// ByAge 类型，用于实现排序接口
type ByAge []Person

func (a ByAge) Len() int           { return len(a) }
func (a ByAge) Swap(i, j int)      { a[i], a[j] = a[j], a[i] }
func (a ByAge) Less(i, j int) bool { return a[i].Age < a[j].Age }
