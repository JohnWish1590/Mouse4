# mouse4 🖱️

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Status](https://img.shields.io/badge/Release-v1.0.0-orange)

**mouse4** 是一款专为 Windows 11/10 设计的高效导航工具。
它的核心功能非常纯粹：**在资源管理器的“空白处”双击左键，自动返回上一层文件夹。**

> 告别瞄准细小的“向上”箭头，让文件浏览如丝般顺滑。

## ✨ 核心功能 (Features)

* **👆 空白处导航**：
    在文件夹背景空白处双击，程序会模拟 `Alt+Up` 快捷键，立刻返回上一级目录。
* **🛡️ 智能防误触 (V4 核心引擎)**：
    * **底层能力检测**：采用 Windows UI Automation 技术，通过 `SelectionItemPattern` 精准识别点击对象。
    * **全方位排除**：无论是点击文件、文件夹、驱动器图标 (如 D盘)、文字、图片还是容量进度条，程序都能识别出它们是“内容”并自动忽略，**绝不干扰正常点击**。
* **⚡ 极速静默**：
    基于多线程与消息队列 (Queue) 设计，极低资源占用，后台静默运行。

## 📥 下载与安装 (Download)

1.  点击页面右侧的 **[Releases](../../releases)** (发行版) 链接。
2.  下载最新的 `mouse4.exe` 文件。
3.  **运行**：双击下载的 exe 文件即可（程序启动后会显示一个黑色日志窗口，最小化即可）。
4.  **退出**：在黑色窗口中按 `Ctrl+C` 或直接关闭窗口。

## ⚙️ 配置说明 (Configuration)

如果你需要调整灵敏度，可以修改源码 `main.py` 顶部的配置：

```python
DOUBLE_CLICK_THRESHOLD = 0.25  # 双击判定速度 (秒)，数值越小要求点得越快
DEBUG_MODE = True              # 设置为 False 可关闭黑框里的日志输出