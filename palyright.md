## Playwright 库简介与使用

Playwright 是由微软推出的一款现代化 Web 应用端到端测试工具，支持多种浏览器（Chromium、WebKit 和 Firefox）以及多种语言（如 Python、JavaScript、Java 等）。它以其强大的功能和灵活性，成为自动化测试领域的重要工具。

安装与配置

在 Python 中使用 Playwright 需要先安装相关依赖。以下是安装步骤：

```
# 使用 pip 安装 Playwright
pip install playwright
# 安装浏览器驱动（Chromium、Firefox 和 WebKit）
playwright install
```

安装完成后，即可在脚本中导入 Playwright 并启动浏览器。

基本用法示例

以下是一个简单的示例，展示如何使用 Playwright 打开网页并截取屏幕截图：

```
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
   # 启动 Chromium 浏览器
   browser = p.chromium.launch(headless=True)
   page = browser.new_page()
   # 打开目标网页
   page.goto("https://playwright.dev/")
   # 截取屏幕截图
   page.screenshot(path="example.png")
   # 关闭浏览器
   browser.close()
```

如果需要异步操作，可以使用 *async_playwright*，结合 *asyncio* 实现异步调用。

核心功能

**跨浏览器支持**：支持 Chromium、WebKit 和 Firefox，适用于桌面和移动设备。**自动等待**：Playwright 会自动等待元素可操作，避免手动设置超时。**测试隔离**：每个测试运行在独立的浏览器上下文中，确保数据隔离。**调试工具**：提供调试器（Playwright Inspector）和跟踪查看器（Trace Viewer），便于排查问题。**脚本录制**：通过命令 *playwright codegen* 快速生成测试脚本。

断言与定位

Playwright 提供了强大的断言和定位功能。例如，使用 *expect* 函数进行断言：

```
from playwright.sync_api import expect
page.goto("https://example.com")
expect(page).to_have_title("Example Domain")
```

定位器用于查找页面元素并执行操作：

```
page.locator("text=Learn more").click()
```

调试与测试运行

Playwright 支持无头模式和有头模式运行测试。以下是一些常用命令：

```
# 运行测试
pytest test_script.py
# 使用有头模式运行
pytest --headed test_script.py
# 指定浏览器运行
pytest --browser=firefox test_script.py
```

