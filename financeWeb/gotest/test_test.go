// test_test.go 文件
package gotest // 测试文件也属于同一个包

import (
	"fmt" // 导入 fmt 用于打印信息 (可选)
	"testing" // 必须导入 testing 包
)

// TestDivision 是一个测试函数，名称必须以 Test 开头，参数为 *testing.T
func TestDivision(t *testing.T) {
	// 正常情况测试
	result, err := Division(10, 2)
	if err != nil {
		t.Errorf("Division(10, 2) 出现错误: %v", err) // 如果出错，报告错误
	}
	if result != 5.0 {
		t.Errorf("Division(10, 2) 期望结果为 5.0, 得到 %f", result) // 如果结果不符，报告错误
	}
	fmt.Println("TestDivision - Normal case passed.") // 辅助信息

	// 除数为0的情况测试
	result, err = Division(10, 0)
	if err == nil {
		t.Errorf("Division(10, 0) 期望出现错误，但没有错误") // 如果没有出错，报告错误
	} else {
        // 检查错误信息是否符合预期
        expectedErr := "除数不能为0"
        if err.Error() != expectedErr {
            t.Errorf("Division(10, 0) 错误信息期望是 '%s', 得到 '%s'", expectedErr, err.Error())
        }
		fmt.Println("TestDivision - Division by zero case passed.") // 辅助信息
	}
}