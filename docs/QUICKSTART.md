# 快速开始（部署指南）

> Mouse4 使用者的极简部署手册。完整使用说明见仓库根目录 `README.md`。

## 0. 一句话结论

运行 Mouse4 **只需要 Windows + Python 3.10+ 环境（或直接使用 Release 中的 exe）**。**不需要安装，不写注册表，默认不联网。**

## 1. 前置条件

- ✅ **操作系统**：Windows 10 / Windows 11
- ✅ **方式一（源码）**：Python 3.10+，依赖见 `requirements.txt`
- ✅ **方式二（推荐）**：Release 中下载 `Mouse4.exe` 直接运行

## 2. 源码运行

```powershell
pip install -r requirements.txt
python main.pyw
```

## 3. 打包 exe

```powershell
python -m PyInstaller Mouse4_onefile.spec
# 或
python -m PyInstaller Mouse4_onedir.spec
```

## 4. 验证运行

- 系统托盘出现 Mouse4 图标。
- 按默认热键 `Ctrl + Shift + 4` 进入截图模式。
- 框选区域后自动复制到剪贴板；若设置了「自动保存目录」，会同时存图。

## 附：小白用户最短路径

下载 Release 中的 `Mouse4.exe` → 双击运行 → 托盘出现图标 → `Ctrl + Shift + 4` 截图。
