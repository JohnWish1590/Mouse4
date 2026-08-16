# Mouse4（鼠标增强 + 跨屏截图工具）

一个简单、纯粹的 Windows 鼠标增强程序：**资源管理器双击返回** + **多显示器（混合 DPI）跨屏高清截图与标注**。

当前版本 **V107.0**。

<p align="center">
  <img src="https://img.shields.io/badge/version-V107.0-green.svg" alt="Version V107.0">
  <img src="https://img.shields.io/badge/platform-Windows-blue.svg" alt="Platform Windows">
  <img src="https://img.shields.io/badge/Python-3.12-orange.svg" alt="Python 3.12">
</p>

---

## 📦 本次发布（V107.0）：两种构建版本

同一个源码（`main.pyw`）构建出两种形态，**功能与行为完全一致**，按使用场景二选一：

| 版本 | 位置 | 体积 | 启动速度 | 适用场景 |
|---|---|---|---|---|
| **单文件版（onefile）** | `dist\Mouse4.exe` | 约 58 MB | 较慢（每次运行先解压到临时目录） | 便携、拷贝单个文件分发 |
| **目录版（onedir）** ⭐推荐 | `dist\Mouse4\Mouse4.exe` | 引导 6.4 MB + `_internal\` 资源目录 | **快**（无需解压） | 日常固定使用，放在固定目录后启动即用 |

**目录版使用注意**：`dist\Mouse4\` 是**一个整体**，`Mouse4.exe` 和 `_internal\` 必须放在一起移动/分发，不能只拷 exe。

两者均由同一份 `main.pyw` 构建（`mouse4.spec` / `mouse4_onedir.spec`），因此**行为、日志、配置完全一致**。构建方法见下文「构建」。

---

## 🛠 开发与更新约定（重要）

- **更新直接在本目录进行**：以后所有功能更新、Bug 修复、文档与打包，一律直接在 `D:\SynologyDrive\CODING\Mouse4` 修改，**不再使用任何副本/临时目录**（历史测试副本 Mouse5 已废弃，仅作备份）。
- **标准流程**：编辑 `main.pyw` → 同步更新 `CHANGELOG.md`、`RELEASE_NOTE.md`、`README.md` → 在**本目录**重新打包（见「构建」）→ 提交并推送 GitHub。
- **必须遵守**「📁 目录与源文件规则」中的版本迭代规则：版本号三处同步（docstring / 启动日志 / CHANGELOG）、发布新版本时先存档 `main.V{新版本号}.pyw`、onefile 与 onedir 双版本同出。
- git 提交/推送由维护者负责；源码修改后工作区保持 dirty 状态供提交，不要自行改动 `.git`。

---

## ✨ 核心功能

### 1. 鼠标增强
- **双击空白返回**：在资源管理器（文件夹）空白处双击左键，自动返回上一级文件夹。内置"不死"守护机制（pynput 监听 + uiautomation 判定），长时间休眠唤醒后依然生效。

### 2. 多显示器跨屏截图（Ctrl + 1）
- **物理像素级高清抓取**：对每块屏独立抓取（逐屏 BitBlt），再按物理偏移拼接成整块虚拟画布——**原生分辨率输出**。
- **混合 DPI 全面支持**：不同分辨率、不同缩放比例（如 150% 主屏 + 100% 副屏）、竖屏/横屏混排均可正确跨屏拖拽选区；进程为 Per-Monitor V2 DPI 感知，跨屏窗口不被 Windows 拉伸。
- **选区钳制**：松手/保存时选区自动钳制到"显示器联合区域"，不会把屏间空隙（无显示器的区域）截进图里。
- **工具栏智能定位**：优先显示在选区下方；下方放不下或落在无显示器空隙带时，自动翻到选区上方；再不行则贴入选区内侧顶部——**选区在屏幕最底部也一定看得到工具栏**。
- **极速完成**：选区内**双击左键**立即保存；或点工具栏 ✓；右键取消。
- **保存 + 剪贴板双通道**：保存高清 PNG 到指定目录（默认 `图片\Mouse4Captures`，文件名 `Mouse4_时间戳.png`），同时复制到剪贴板（优先 Qt 通道，失败自动降级 PIL/DIB 并重试 3 次）。
- **绘图标注**：矩形、椭圆、箭头、画笔、文字，8 色板 + 字号调节 + 撤销。
- **配置记忆**：自动记住上次的画笔颜色、字号、保存目录（`%APPDATA%\Mouse4\config.json`）。

### 3. 右键直接存图
注册后，在任意文件夹空白处右键 → 「粘贴刚才的截图 (Mouse4)」，即可把剪贴板图片保存为 PNG 到该文件夹（走 `--paste` 轻量模式，不干扰主程序）。

### 4. 稳定性设计（历史重点修复）
- **睡眠唤醒免疫**：原生 `RegisterHotKey` + 自动重试（最多 10 次）；看门狗检测到时间跳变后自动重启（三角色架构：main / paste / restart-wait）。
- **单实例保护**：Windows 命名 Mutex，防止多实例并存。
- **崩溃拦截网**：主线程/后台线程异常均写入日志并弹窗提示，不留黑箱。
- **托盘常驻**：强引用防止 GC 回收导致图标消失。

---

## 🖱 使用说明

1. 运行 `Mouse4.exe`（单文件版）或 `Mouse4\Mouse4.exe`（目录版），托盘出现图标。
2. 按 **Ctrl + 1** 进入截图：跨屏拖拽选区 → 双击完成（或 ✓）。
3. 标注：选矩形/椭圆/箭头/画笔/文字，调颜色字号，↶ 撤销。
4. 完成后自动：保存 PNG（提示保存路径）+ 复制到剪贴板。
5. 托盘菜单：立即截图 / 重启程序(修复) / 注册·移除右键菜单 / 截图保存目录… / GitHub / 退出。

### 快捷键与鼠标
| 操作 | 效果 |
|---|---|
| `Ctrl + 1` | 全局热键，开始/切换截图 |
| 左键拖拽 | 选择区域 |
| 选区内双击 | 立即保存并关闭 |
| 右键 | 取消当前标注 / 取消截图 |
| 资源管理器空白处双击 | 返回上一级文件夹 |

---

## 🖥 多显示器与 DPI 技术说明

- **物理像素模式**：代码禁用 Qt 高 DPI 缩放（`QT_ENABLE_HIGHDPI_SCALING=0` 等），使 `QScreen::geometry()` 与 mss 抓取均为物理像素、完全一致，画布/窗口/鼠标/选区 1:1 对齐。
- **逐屏抓取拼接**：对每块屏分别 `mss.grab()`（各屏独立 BitBlt），按物理偏移贴入虚拟画布；避免"单次整块虚拟桌面 BitBlt"在混合 DPI 下产生接缝缩放垃圾（历史上导致截图最左侧出现白乱码条）。
- **已知限制（HDR）**：GDI（mss）无法抓取 **HDR 显示器**内容（会整屏黑）。启动截图后如日志出现 `WARNING ... grab all-black ... need DXGI`，说明该屏为 HDR，当前版本暂不支持（需 DXGI 桌面复制方案，属后续规划）。

---

## 📜 日志与排障

- 日志文件：`%APPDATA%\Mouse4\debug.log`（**倒序**：最新日志在文件顶部；超过 30 天的自动裁剪，`[FATAL CRASH]` 永久保留）。
- 每次截图会记录 `[Shot]` 行：每屏 `screen 宽x高 dpr=.. phys=.. lum=(min,max)`、画布尺寸、显示器数量。
- 常见排查：
  - 启动即退出 → 查看日志是否 `[Mutex] Another instance already running`（旧进程未退）。
  - 某屏截图全黑 → 看该屏日志 `lum=(0,0)` 是否为 HDR（见上）。
  - 热键不响应 → `[Hotkey] RegisterHotKey ...` 行是否失败/重试。

---

## 🔨 构建（开发者）

### 环境
- Windows 10/11，Python 3.12（3.12.2 验证）
- 依赖：`pip install -r requirements.txt`（uiautomation / pynput / pyinstaller / Pillow / mss / PyQt6 / pywin32）

### 打包命令（在项目根目录）
```powershell
# 单文件版 → dist\Mouse4.exe
python -m PyInstaller mouse4.spec --noconfirm

# 目录版 → dist\Mouse4\
python -m PyInstaller mouse4_onedir.spec --noconfirm
```
> ⚠️ 打包前请先**退出正在运行的实例**（Windows 会锁定正在运行的 exe，导致 `PermissionError: [WinError 5]` 覆盖失败）。

### 源码直接运行
```powershell
python main.pyw
```

---

## 📁 目录与源文件规则

```
Mouse4/
├── main.pyw              # 当前版本源码（唯一活跃源文件，随版本迭代修改）
├── archive/              # 历史版本源码快照（只读存档，不参与构建）
│   ├── main.V40.pyw
│   ├── main.V47.pyw
│   ├── main.V54.pyw
│   ├── main.V61.pyw
│   ├── main.V66.pyw
│   └── main.V107.pyw
├── mouse4.spec           # PyInstaller 单文件版(onefile) 构建配置
├── mouse4_onedir.spec    # PyInstaller 目录版(onedir) 构建配置
├── requirements.txt      # 构建/运行依赖清单
├── logo.ico              # 托盘图标 / exe 图标资源
├── CHANGELOG.md          # 版本变更记录（最新版本在顶部）
├── README.md             # 本文档
├── RELEASE_NOTE.md       # 发布说明汇总（V107/V103/V90，最新在最上）
├── _diag.py              # 显示器/DPI 诊断脚本（排障用，见下）
├── dist/                 # 构建产物：Mouse4.exe（单文件版）+ Mouse4/（目录版）
└── build/                # PyInstaller 中间产物（可随时删除）
```

**版本迭代规则（务必遵守）**
1. 当前活跃代码永远在 `main.pyw`。
2. 发布新版本时，先把当前 `main.pyw` **存档复制**为 `main.V{新版本号}.pyw`（如发布 V108 前：`copy main.pyw archive/main.V108.pyw`），再继续在 `main.pyw` 上开发。快照文件只读，不再修改。
3. 版本号在 **三处同步**：`main.pyw` 头部 docstring、启动日志 `=== Mouse4 Vxxx Started ===`、`CHANGELOG.md` 最新条目。
4. 每次功能变更必须在 `CHANGELOG.md` 顶部新增条目（格式：`## [V版本号] - 日期 (简述)`，含 Added / Fixed / Changed / Root Cause），并同步更新 `RELEASE_NOTE.md` 对应版本段落（汇总发布说明，最新在最上）。
5. 同一版本必须同时产出 onefile 与 onedir 两种构建（同源，行为一致）。
6. 打包产物 `dist/`、`build/`、`*.spec` 已被 `.gitignore` 忽略，不提交 git；git 只跟踪源码与文档。

**诊断脚本 `_diag.py`**
打印真实显示器布局（Qt 几何、DPI、主屏）与 mss 逐屏抓取亮度统计，用于定位多屏/DPI/HDR 问题：
```powershell
python _diag.py
```

---

## 🏗 架构简述

- **截图核心**：单窗口覆盖整个虚拟桌面 → 逐屏 mss 抓取 → 物理像素画布 → 选区/标注/裁剪统一虚拟桌面坐标。
- **热键**：原生 `RegisterHotKey` 两阶段（注册不依赖 QApp；QApp 就绪后再进 `GetMessageW` 消息循环，事件同步）。
- **重启**：三角色架构——`main`（主程序，持 Mutex）/ `--paste`（右键存图，绕过 Mutex）/ `--restart-wait`（看门狗重启 helper，等旧进程死透再拉起新进程）。
- **单实例**：命名 Mutex `Mouse4_SingleInstance_JohnWish`。
- **崩溃拦截**：`sys.excepthook` + `threading.excepthook` → 日志 + 弹窗。

---

## 仓库链接

- 📦 源码 / Issues / Releases: [https://github.com/JohnWish1590/Mouse4](https://github.com/JohnWish1590/Mouse4)
- 🦕 问题反馈: [GitHub Issues](https://github.com/JohnWish1590/Mouse4/issues)
- 📝 变更历史: [CHANGELOG.md](CHANGELOG.md)
- 🚀 发布说明: [RELEASE_NOTE.md](RELEASE_NOTE.md)
- ⚡ 快速开始（部署细节）: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- 🔒 隐私政策: [PRIVACY.md](PRIVACY.md)
- 🏪 上架清单（未来）: [STORE_GUIDE.md](STORE_GUIDE.md)

Socials: @下一站澳门. DM for inquiries.
