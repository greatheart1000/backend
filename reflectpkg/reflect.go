package reflectpkg

import (
	"fmt"
	"reflect"
)

// printTypeAndValue 动态打印类型和值
func PrintTypeAndValue(v interface{}) {
	t := reflect.TypeOf(v)
	fmt.Printf("Type: %s\n", t)

	val := reflect.ValueOf(v)
	fmt.Printf("Value: %v\n", val)

	if t.Kind() == reflect.Struct {
		for i := 0; i < t.NumField(); i++ {
			field := t.Field(i)
			fieldValue := val.Field(i)
			fmt.Printf("Field %s (%s) = %v\n", field.Name, field.Type, fieldValue)
		}
	}
}

// modifyValue 动态修改值（仅限指针）
func ModifyValue(ptr interface{}) {
	val := reflect.ValueOf(ptr)
	if val.Kind() != reflect.Ptr || val.IsNil() {
		fmt.Println("Error: Must pass a non-nil pointer")
		return
	}
	// 使用 Elem() 获取指针指向的值
	elem := val.Elem()
	// 检查是否可以修改
	if !elem.CanSet() {
		fmt.Println("Error: Cannot set value")
		return
	}
	// 修改值，假设我们知道 elem 的类型
	switch elem.Kind() {
	case reflect.String:
		elem.SetString("ModifiedName")
	case reflect.Int:
		elem.SetInt(99)
	}
}
