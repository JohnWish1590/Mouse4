# Mouse4

一个简单、纯粹的 Windows 鼠标增强程序。它只有两个核心功能：双击返回 和 截图。

<p align="center">
  <img src="https://img.shields.io/badge/version-V75.0-green.svg" alt="Version V75.0">
  <img src="https://img.shields.io/badge/platform-Windows-blue.svg" alt="Platform Windows">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License MIT">
</p>

## ✨ 核心功能

### 1. 鼠标增强
* **双击空白返回**：在资源管理器（文件夹）的空白处双击鼠标左键，自动返回上一级文件夹。内置“不死”守护机制，即使系统长时间休眠，唤醒后依然稳定生效，让文件浏览操作更顺手。

### 2. 高清截图与标注
按下快捷键（默认 `Ctrl + 1`）即可触发物理像素级的高清截图。
* **睡眠免疫**：独创后台“微创重连”机制，电脑无论休眠/睡眠多久，唤醒后快捷键 100% 稳定响应，不崩溃、不失效。
* **跨屏截图**：完美支持多显示器环境，支持在不同屏幕之间自由拖拽选区，智能识别当前屏幕上下文。
* **极速保存**：选区完成后，在区域内**双击鼠标左键**即可瞬间保存并关闭；底层采用原生 DIB 格式写入剪贴板，彻底杜绝“截图后粘贴为空”的问题。
* **绘图标注**：提供矩形、圆形、箭头、画笔等常用工具。
* **文字输入**：点击屏幕任意位置即可直接输入文字，支持字号实时调整。
* **配置记忆**：自动持久化保存您上次使用的画笔颜色和字号，下次截图无缝衔接。
* **右键直接存图**：截图后，在任意文件夹空白处通过系统右键菜单，可直接将剪贴板里的图片“粘贴”保存为本地 PNG 文件。

---

## 📥 下载与使用

### 方式一：直接运行 (推荐)
1.  前往 [Releases 页面](../../releases) 下载最新的 `Mouse4.exe`。
2.  直接双击运行即可（建议放入一个固定文件夹，如 `D:\Program Files\Mouse4`）。

### 方式二：源码运行
```bash
git clone [https://github.com/你的用户名/Mouse4.git](https://github.com/你的用户名/Mouse4.git)
cd Mouse4
pip install -r requirements.txt
python main.pyw

📬 联系作者
如果你有任何建议、发现 Bug，或者只是想交个朋友，欢迎扫描下方二维码加我微信：

<div align="left"> <img src="wechat_qr.png" alt="WeChat QR Code" width="200" /> </div>

Created with ❤️ by JohnWish