# Changelog

All notable changes to the Mouse4 project will be documented in this file.

## [V107.1] - 2026-08-17 (截图触发残留修复 + 自动保存修复 + 14天自动清理)
### Fixed
- **截图框被系统粘贴板抢焦点后误关闭**: `do_show_windows()` 原 toggle 逻辑
  `if active_windows: close_all_windows(); return` 在系统粘贴板(Win+V)抢走前台焦点后，
  SnippingWindow 已在背后弹出(active_windows 残留非空)，用户看不到再按一次即命中关闭分支、
  直接 return，截图框永远不出现。改为 `if active_windows: close_all_windows()`
  (每次按都先关旧的、再开新的)，消除误关。
- **截图自动保存到磁盘失败**: `GlobalConfig.screenshot_dir` 是 @property，
  代码误写成方法调用 `config.get_screenshot_dir()` 抛 AttributeError，保存文件一直失败、
  只剩剪贴板可用。两处改为 `config.screenshot_dir`(自动保存 + 选目录对话框)。
### Added
- **截图自动清理**: 新增 `cleanup_old_screenshots(keep_days=14)`，扫描保存目录、
  解析文件名时间戳、删除超过 14 天的 `Mouse4_*.png`；每天最多执行一次。
  触发点: 截图保存后 + 程序启动时后台线程。
> 注: 本次 3 个 commit 尚未在 `main.pyw` 内升级版本号(仍显示 V107)，正式发布时统一升为 V107.1。

## [V107.0] - 2026-08-15 (物理像素逐屏抓取 + 工具栏定位重写)
### 📦 发布物（本次双版本 + 品牌回归 Mouse4）
- **品牌回归**: 项目名从开发代号 Mouse5 统一回归 **Mouse4**——exe 名、打包 spec（`mouse4.spec` / `mouse4_onedir.spec`）、截图文件名前缀（`Mouse4_*.png`）、默认截图目录（`图片\Mouse4Captures`）全部改为 Mouse4*。
- **单文件版 (onefile)**: `dist\Mouse4.exe`（约 58MB，便携，启动较慢）。
- **目录版 (onedir)** ⭐: `dist\Mouse4\`（引导 6.4MB + `_internal\`，启动快，日常推荐）。
- 两版本由同一 `main.pyw` 同源构建，功能与行为完全一致。
### Root Cause (实测诊断)
- 实测 3 屏布局: 左 2K 竖(150%缩放, 物理2160x3840) / 中 2K 横(150%, 3840x2160, 主屏) /
  右 1080p 横(100%, 1920x1080) — **混合 DPI 且各屏位置带偏移**。
- **V106 左右黑屏根因**: 开启 Qt 缩放后 `QScreen::geometry()` 返回"物理位置 + DIP 尺寸"
  的混合坐标(实测: 左屏报位置 -2160,-1001 但尺寸 1440x2560), DIP 画布拼接全部错位。
  V107 恢复物理像素模式后 geometry 全为物理像素, 与 mss monitors[0] 完全一致。
- **旧 V105 白条根因**: 单次整块虚拟桌面 BitBlt 在混合 DPI 下产生接缝缩放垃圾。
  逐屏抓取后各屏独立 BitBlt, 按物理偏移拼接, 白条消失(实测逐屏抓取亮度全部正常)。
### Changed
- **恢复物理像素模式**(重新禁用 Qt 缩放): `QScreen::geometry()` 与 mss 同为物理像素,
  画布/窗口/鼠标/选区 1:1 对齐; 进程保持 Per-Monitor V2 感知, 跨屏窗口不被 Windows 拉伸。
- **工具栏定位重写**: 候选位置依次为 选区下方 → 选区上方 → 选区内侧顶部,
  每个候选必须"完全在窗口内且不落在无显示器空隙带"。修复: 选区贴近屏幕底部时
  工具栏落入下方空隙带(短屏下方无屏幕)导致看不见的问题。
- onefile 与 onedir 同源构建, 行为一致。
### Fixed
- V106 左右屏黑屏/错位。
- V105 截图最左侧白条(混合 DPI 接缝垃圾)。
- 选区在屏幕底部时工具栏不显示。
### Changed
- 版本号 V106.0 → V107.0

## [V106.0] - 2026-08-15 (混合 DPI 跨屏重构 + onedir 打包)
### Changed
- **启用 Qt per-monitor DPI 托管**: 移除 `QT_ENABLE_HIGHDPI_SCALING=0` / `QT_AUTO_SCREEN_SCALE_FACTOR=0`。
  Windows 会对跨不同 DPI 屏幕的窗口内容做位图拉伸，Qt 忽略 WM_DPICHANGED 时窗口比例错乱、
  坐标错位、显示不全。现在由 Qt 按每屏 DPR 渲染，坐标统一为逻辑像素(DIP)。
- **画布改为逐屏抓取再拼接**(对齐 Flameshot/ShareX 做法): 每块屏 mss 单独抓物理像素 →
  按 DPR 缩放到 DIP → 按逻辑偏移拼成虚拟画布。不再用单次整块虚拟桌面 BitBlt
  (混合 DPI 下会黑屏/拉伸)。QScreen 与 mss 监视器按物理位置重叠配对，顺序无关。
- **打包方式**: 改用 onedir(`dist/Mouse5/`, `Mouse5_onedir.spec`)，启动显著变快，
  且没有 onefile 的 `_MEI` 临时目录问题(V101 的 env 重置逻辑保留但不再必要)。
### Fixed
- **左缘 1-2 条像素乱**(保存图): 旧实现 `scale_factor=抓屏宽/窗口宽` 略≠1 时
  drawPixmap 拉伸插值 + 裁剪 int() 取整在左边缘错位。V106 画布按窗口 DIP 尺寸精确构造，
  scale_factor 恒为 1，像素级对齐。
- **三屏中间黑**: 逐屏抓取消除单次 BitBlt 的混合 DPI 黑块隐患；若为"包围盒空隙"
  (中间屏比两侧矮/有垂直偏移)，保存结果里空隙天然为黑(所有工具一致)，V106 新增
  **选区自动钳制到显示器联合区域**，跨屏拖拽不再把空隙截进图里。
- **混合分辨率下工具栏/选区落进无显示器空隙带看不见**: 工具栏中心点不在任何真实
  显示器区域时自动翻到选区上方。
### Added
- **HDR/黑屏诊断**: 每屏抓取后采样亮度范围写入日志；某屏全黑(lum=(0,0))时输出
  `WARNING ... possible HDR/bit-depth issue, need DXGI`，用于确认是否需要 DXGI 抓屏。
### Changed
- 版本号 V105.0 → V106.0

## [V105.0] - 2026-08-15 (单虚拟画布跨屏截图 + 剪贴板修复)
### Added
- **单虚拟画布架构**: 截图时只创建一个覆盖整个虚拟桌面的窗口(所有显示器 `geometry()` 并集)，
  mss 一次性抓取 `monitors[0]`(全部显示器拼接区域, 支持负坐标)作为完整画布。
  选区/标注/保存统一使用虚拟桌面坐标系，跨屏拖拽选区在任意两块屏之间连续可用。
### Fixed
- **跨屏截图出错**: V66 changelog 声称的"虚拟画布拼接"实际从未实现(V54/V61/V66/V104 均为
  每屏一个独立窗口、各自独立选区)。跨屏拖拽时选区和画面只存在于按下鼠标的那一个窗口，
  保存时用越界矩形裁剪单屏截图 → 第二块屏无高亮、保存结果残缺/错位/黑边。本次重构彻底修复。
- **复制到剪贴板失效**: `_do_save_sync` 提前 `return saved_path`，V91 设计的剪贴板写入代码
  成为死代码，"已复制到剪贴板"从未真正发生。重构为保存文件 + 复制剪贴板(优先 Qt，
  PIL/DIB 3 次重试兜底)都执行，并新增裁剪结果有效性校验。
- **工具栏命中检测坐标错位**: `mapToGlobal()` 与窗口本地 `geometry()` 比较，在窗口原点
  非 (0,0)(副屏/负坐标)时永远判定"不在工具栏上"。改为本地坐标比较。
- **工具栏右侧越界**: 选区贴近虚拟桌面右缘时工具栏可能溢出窗口不可见，增加右缘钳制。
### Changed
- 版本号 V104.0 → V105.0
- 截图性能: 每次触发从 N 次抓屏(N=屏幕数, 3 屏约 460ms)降为 1 次抓屏(约 200ms)。
- `showFullScreen()` → `show()`: 全屏状态会被 Windows 钉在单块屏上，跨屏窗口必须用
  普通显示 + 显式几何。

## [V104.0] - 2026-07-28 (灰屏修复 + 日志倒序)
### Fixed
- **首次截图灰屏**: showFullScreen() 先画了灰色遮罩再 grab_current_screen()，
  mss 截到的是遮罩而非屏幕内容。将 grab_current_screen() 移到 showFullScreen() 之前，
  确保截图的是原始屏幕内容而不是自己的遮罩层。
### Changed
- **debug.log 倒序**: 最新日志写入文件头而不是文件尾，文字越狱查看时不再需要滚动到底部。
- 版本号 V103.0 → V104.0

## [V103.0] - 2026-07-26 (截图白屏崩溃修复 - full_screenshot 初始化时序)
### Fixed
- **截图白屏后崩溃**: `showFullScreen()` 立即触发 `paintEvent`，但此时 `full_screenshot`
  尚未初始化(在构造函数后续行才赋值)，导致 `AttributeError: no attribute full_screenshot`。
  修复: 所有属性初始化移到 `showFullScreen()` 之前。
### Changed
- 版本号 V102.0 → V103.0

## [V102.0] - 2026-07-22 (箭头崩溃修复 + 30天日志裁剪)
### Fixed
- **箭头绘制崩溃**: `draw_arrow` 中 `end` 是 `QPoint` 但减 `QPointF` 时报 `TypeError`，
  导致截图标注使用箭头后崩溃弹窗。修复: 函数开头统一转 `QPointF`。
### Added
- **30 天日志自动裁剪**: 写入日志时自动清理超过 30 天的记录，
  `[FATAL CRASH]` 行永久保留。每天最多执行一次，无性能开销。
### Changed
- 版本号 V101.0 → V102.0

## [V101.0] - 2026-05-17 (PyInstaller onefile env fix - _MEI resurrection)
### Root Cause (codex analysis)
V99-V100 sleep wake restart failure: not Python exception, not Qt conflict.
Red dialog: `Failed to start embedded python interpreter!`
Yellow dialog: `Failed to remove temporary directory`

**PyInstaller onefile classic pitfall**: onefile extracts to `_MEIxxxxx` temp dir.
Child via Popen inherits parent's `_MEI` env. Parent exits and cleans `_MEI`,
but child still uses it - bootloader fails to start embedded Python.
proc.poll() returns None (OS process alive) but Python never runs.

### Changed
- `PYINSTALLER_RESET_ENVIRONMENT=1`: Set on all outlive-parent Popen calls
  (helper launch, main launch). Child creates independent `_MEI` temp dir.
- `_reset_env()` helper: encapsulates env logic, frozen-mode only.
- onefile + env var is minimal fix; onedir would avoid this entirely.

## [V100.0] - 2026-05-17 (可观测重启版 - Observable Restart)
### Fixed
- **V99 重启黑箱**: V99 的 helper 声称 "New main instance launched" 但新主进程从未留下启动日志。helper 立即退出，旧进程也已不在，程序彻底消失。
- **黄色/红色弹窗**: 新主进程在系统未完全恢复时启动，Qt 初始化/显卡驱动等失败 → `global_exception_handler` 红叉 + `thread_exception_handler` 黄叹号，进程瞬间崩溃。
### Added
- **角色标注启动日志**: 每条 `=== Mouse4 V100 Started ===` 现在标明 `role=main` / `role=restart-wait` / `role=paste`，一眼看出哪个角色在跑。
- **helper 沉降延迟**: helper 等旧进程退出后额外等待 3 秒，让睡眠唤醒后的系统服务/驱动/用户会话充分恢复再拉主进程。
- **helper 启动重试**: Popen 新主进程后等 2 秒确认进程存活。如果 2 秒内退出则自动重试，最多 3 次。
- **显式 cwd 设置**: helper 启动主进程时指定 `cwd` 为 exe 所在目录，防止睡眠后工作目录异常导致资源加载失败。
### Changed
- 版本号 V99.0 → V100.0
- 现在如果再次失败，日志会直接记录 `New main PID xxxx exited early with code ...` 和重试次数，不再黑箱。

## [V99.0] - 2026-05-17 (正式版 - Official Release)

V77→V99 睡眠唤醒问题修复全历程。V90 之前的原生热键退化导致了一系列睡眠唤醒崩溃，经过 codex 深度 code review 和 6 轮迭代，最终以三角色重启架构收口。

### V77 原始问题 (2026-02-26)
- Watchdog 检测到睡眠 → Hard Restart → 新进程启动后热键失效、剪贴板崩溃
- 黄色/红色双弹窗，需手动重启才能恢复

### V91 修复链
- **RegisterHotKey 重试**: 旧进程热键未释放时自动重试 10 次(间隔 1s)
- **Qt 剪贴板优先**: `QApplication.clipboard().setPixmap()` 优先，DIB 方式 3 次重试兜底
- **移除 keyboard 依赖**: `press_and_release('backspace')` → `win32api.keybd_event`

### V92 热键线程提前
- 热键线程在 `QApplication(sys.argv)` 之前启动，不等 QApp
- 否则睡眠恢复后 QApp 初始化挂起 → 热键线程永不启动

### V93 Popen 替代 startfile
- `os.startfile` 走 Explorer，睡眠后 Explorer 未就绪 → 新进程静默消失
- `subprocess.Popen` + `DETACHED_PROCESS` 直接调用 NT 进程创建 API

### V94 架构加固 (引入单实例 Mutex)
- `threading.Lock` → `threading.RLock` (set() 调 _save_sync() 不卡死)
- Windows 命名 Mutex 防多进程并存
- `os._exit(0)` → `QApplication.quit()` (Qt 清理托盘/hook)

### V95 问题暴露 (codex review)
- **P0 - 重启被 Mutex 挡死**: 旧进程持 Mutex，新进程 CreateMutex → ERROR_ALREADY_EXISTS → exit
- **P0 - paste 被拦截**: `Mouse4.exe --paste "%V"` 先撞 Mutex 后 exit，右键粘贴全废
- 修复: `CloseHandle(h_mutex)` → `Popen` → `quit()`，但本质上是拆掉安全带重启

### V96 问题暴露 (codex review)
- **P0 - paste NameError**: `run_paste_mode_safe()` 调用在函数定义之前，运行时崩
- codex 提出三角色重启架构方案

### V97 三角色重启架构 (codex 方案落地)
- **普通模式**: CreateMutex → 拿不到就退出 (单实例保护)
- **paste 模式**: 绕过 Mutex，存剪贴板到文件 → exit (短命工具进程)
- **restart-wait 模式**: 绕过 Mutex，`OpenProcess` + `WaitForSingleObject(10s)` 等旧进程死透
  → 启动新主实例 → exit
- 旧进程持 Mutex 到死，不提前释放。OS 自然释放 → 新进程自然取得。

### V98 硬化 (codex review)
- `QTimer.singleShot` → `threading.Timer` (看门狗线程无 Qt event loop，timer 不触发)
- Win32 API 显式 `argtypes`/`restype` (64 位 HANDLE 不被 `c_int` 截断)

### V99 正式版 (codex final)
- `threading.Timer` 设为 daemon (非 daemon 阻塞进程退出，优雅路径也被拖 3 秒强杀)
- 所有已知问题已收口，codex 终审通过

### 架构总览 (V99)
```
启动:
  1. ConfigManager
  2. --paste?       → run_paste_mode_safe (不碰 Mutex)
     --restart-wait? → run_restart_wait (不碰 Mutex)
  3. CreateMutex    → 已有实例则退出 (单实例保护)
  4. 热键 Phase 1 (RegisterHotKey 重试 ×10)
  5. 看门狗线程 / 鼠标线程
  6. QApp 初始化 → 信号连接 → hotkey_ready.set()
  7. 热键 Phase 2 (GetMessageW 消息循环)

重启:
  旧进程 ─Popen(--restart-wait pid)─→ helper ─Wait(10s)─→ 新主进程
           └─app.quit()+3s daemon timer    └─旧进程死透,Mutex自然释放─┘
```

## [V97.0] - 2026-05-17 (三角色重启架构 - Three-Role Restart)
### Added
- **三角色重启架构**: 引入 `--restart-wait <pid>` helper 进程模式。重启时旧主进程不释放 Mutex，而是启动 helper 等自己死透，helper 再用 Win32 API (`OpenProcess` + `WaitForSingleObject`) 等旧 PID 退出，然后才启动新主实例。全过程 Mutex 由 OS 自然释放，无竞态窗口。
- **`run_restart_wait`**: helper 进程函数，绕过单实例保护。等旧进程退出（10 秒超时兜底），然后启动新主实例，自己退出。
- **重启 3 秒 timer 兜底**: `QTimer.singleShot(3000, os._exit)` 在 `app.quit()` 之上增加强制退出，防止 event loop 卡死后进程不退出。
### Fixed
- **重启不再提前释放 Mutex**: 删除 V95/V96 的 `CloseHandle(h_mutex)` 重启路径，改由 OS 在旧进程死亡时自然释放。消除“锁已空但进程还活着”的竞态窗口。
- **特殊模式统一前置**: `--paste` 和 `--restart-wait` 都在 Mutex 创建之前处理，不碰单实例保护，互不干扰。
- **日志覆盖**: helper 的每个决策点（等到了旧进程退出 / 超时 / 旧进程已不在）都有独立日志。
### Changed
- 版本号 V96.0 → V97.0
- 启动顺序: `ConfigManager` → 特殊模式(paste/restart-wait) → Mutex → 主程序

## [V96.0] - 2026-05-17 (架构加固版 V3 - paste NameError修复)
### Fixed
- **paste 模式必炸 NameError** (P0): `run_paste_mode_safe()` 函数定义在调用之后才出现，Python 执行到调用行时函数名还不存在。将函数定义上移到 paste 判断语句**之前**，消除运行时崩溃。
- 重启 Mutex 竞态窗口已缩小：`CloseHandle` → `Popen` 时序更紧凑。
### Changed
- 版本号 V95.0 → V96.0

## [V95.0] - 2026-05-17 (架构加固版 V2 - Mutex/Paste/QApp兜底)
### Fixed
- **重启被 Mutex 挡死** (P0): `CloseHandle(h_mutex)` 在先, `Popen` 在后，新进程不再因 Mutex 已存在而退出。V94 的致命回归。
- **paste 模式被拦截** (P0): `--paste` 分支移到 Mutex 检查之前，右键粘贴不再因单实例保护而静默退出。
- **看门狗 QApp 未就绪** (P1): `QApplication.quit()` 前增加 `QApplication.instance()` 判断，QApp 未初始化时走 `os._exit()` 兜底。
- **ctypes.wintypes 隐式依赖** (P2): 增加显式 `import ctypes.wintypes`。
### Changed
- 版本号 V94.0 → V95.0

## [V94.0] - 2026-05-17 (架构加固版 - Architecture Hardening)
### Added
- **单实例保护**: Windows 命名 Mutex (`CreateMutexW`), 防止看门狗重启后新旧进程并存。检测到已有实例时自动退出, 日志记录 `[Mutex] Another instance already running`。
- **热键两阶段设计**: Phase 1 注册热键(不依赖 QApp, 提前执行), Phase 2 消息循环(等 QApp 就绪信号再 emit)。通过 `threading.Event()` 同步, 彻底解决信号时序竞态。
### Fixed
- **配置保存死锁**: `threading.Lock` → `threading.RLock`, `set()` 调 `_save_sync()` 时同一线程可重入, 不再卡死。
- **硬退出不清理**: `os._exit(0)` → `QApplication.quit()`, 让 Qt 有机会清理托盘图标和系统 hook, atexit 写入配置, 进程自然退出。
- **源码模式重启路径**: `sys.argv[0]` 改为 `os.path.abspath(sys.argv[0])`, 避免相对路径找不到脚本。
### Changed
- 版本号 V93.0 → V94.0
- `restart_program`: 错误时 `os._exit(1)` 仅作为最后的退路

## [V93.0] - 2026-05-17 (睡眠唤醒终极修复 V3 - Popen Not Startfile)
### Fixed
- **看门狗重启后新进程不启动**: `os.startfile` 通过 Windows Explorer 启动进程，睡眠恢复后 Explorer 可能未就绪，导致新进程静默消失。改用 `subprocess.Popen` + `DETACHED_PROCESS` 直接调用系统进程创建 API，不依赖 Explorer，可靠性显著提升。
### Changed
- 版本号 V92.0 → V93.0
- `restart_program`: `os.startfile` → `subprocess.Popen`

## [V92.0] - 2026-05-16 (睡眠唤醒终极修复 V2 - Hotkey Thread First)
### Fixed
- **热键线程永不启动**: V91 的热键线程在 `QApplication(sys.argv)` 之后启动，睡眠恢复后 QApplication 初始化可能挂起，导致线程根本跑不起来。现在热键线程提到最前面(第一行)，不等 QApp，确保无论系统状态如何都能启动。
- **信号时序安全**: 热键线程启动时信号尚未连接，首次按下 Ctrl+1 会被忽略，但不会报错。一旦 QApplication 就绪、信号连接完成，后续按键正常工作。
### Changed
- 版本号 V91.0 → V92.0
- 启动顺序: 热键线程 → 看门狗 → 鼠标线程 → QApp

## [V91.0] - 2026-05-16 (睡眠唤醒终极修复 - The Ultimate Wake-Up Fix)
### Added
- **RegisterHotKey 自动重试**: 睡眠恢复后旧进程刚 `os._exit`，Windows 还没清理完旧热键，新进程立即注册会失败。现在最多重试 10 次(间隔 1s)，确保热键 100% 注册成功。
- **Qt 剪贴板优先**: 截图保存时优先使用 `QApplication.clipboard().setPixmap()`，睡眠唤醒后比 `win32clipboard.OpenClipboard()` 稳定得多。
- **DIB 方式带 3 次重试**: 如果 Qt 剪贴板失败，自动降级到 DIB 方式并重试 3 次，每次确保 `CloseClipboard`，防止句柄泄漏。
### Fixed
- **睡眠唤醒后热键失效** (Issue #2): 新进程启动后 `RegisterHotKey` 因旧进程热键未释放而失败，导致热键完全不可用。用户需手动重启一次才能恢复。
- **剪贴板崩溃** (Issue #1): `win32clipboard.OpenClipboard()` 在睡眠恢复后抛出 `arguments did not match any overloaded call`，截图后无法保存到剪贴板，弹出红叉错误框。
- **移除 keyboard 模块依赖**: `keyboard.press_and_release('backspace')` 替换为 `win32api.keybd_event`，彻底消除 `keyboard` 模块在 PyInstaller 环境和睡眠场景下的不稳定性。
### Changed
- 版本号 V90.0 → V91.0
- 启动日志从 `V77` 修正为 `V91`

## [V90.0] - 2026-04-30 (终极纯净版 - The Ultimate Clean)
### Added
- **架构精简回滚**: 移除了实验性的延迟加载 (Lazy Load) 和冗余桥接层 (QBuffer/QIODevice)，回归纯净架构。单文件体量更小、运行时依赖更稳固。
- **全域崩溃拦截网 (Black Box)**: 挂载 `sys.excepthook` + `threading.excepthook` 双层拦截器，主线程或后台线程发生未处理异常时自动弹出可视化报警对话框并记录日志，告别静默死亡。
- **系统级强力重启 (Hard Restart)**: 看门狗线程每 5 秒心跳侦测时间跳变，一旦检测到系统深度睡眠唤醒，立即启动全新进程并湮灭旧进程，确保 100% 干净的热键抢占。
- **原生热键接管 (Native Hotkey)**: 彻底废弃第三方 `keyboard` 库，改用 Windows `RegisterHotKey` API 注册全局热键 Ctrl+1。热键直接注册于内核消息队列，不受睡眠唤醒影响。
### Fixed
- **睡眠唤醒 pynput 崩溃**: 将 `pynput` 提前到模块最顶层全局加载，锁定内存地址，彻底解决 Windows 睡眠唤醒后的 `ImportError`。
- **工具栏越界遮挡**: 重写 `show_toolbar` 坐标计算逻辑，选区靠近屏幕底部时工具栏自动翻转到选区上方，防止溢出不可见。
- **托盘图标随机消失**: 在主线程入口建立 `tray_icon_ref` 全局强引用，防止托盘图标被 Python 垃圾回收器 (GC) 错误回收。
- **移除 DPI 冲突告警**: 物理移除手动 DPI 设置调用，完全信任 PyQt6 原生 `Per-Monitor V2` 策略。
### Changed
- 恢复所有重型库的全局前置导入，杜绝单文件 PyInstaller 打包环境下的运行时异常
- 采用 PIL 中转方案精准剥离 BMP 文件头后写入剪贴板 (`CF_DIB`)，确保 100% 粘贴成功率
- 净化日志系统，使用 `QT_LOGGING_RULES` 物理静音 DPI 重复声明的非致命警告

## [V83.0] - 2026-04-06 (Native Hotkey Ultimate)
### Added
- **原生热键接管 (Native Hotkey)**: 彻底废弃第三方 `keyboard` 库，改用 Windows 官方原生 API `RegisterHotKey`。
  - **睡眠绝对免疫**: 热键直接注册于操作系统内核消息队列，而非不稳定的应用层钩子，彻底解决了 Windows 10/11 在睡眠唤醒或锁屏时强行拔除第三方钩子的顽疾。
  - **硬件级零迟滞**: 响应速度大幅提升，按下热键瞬间被内核拦截并分发给程序，彻底消除了“先触发浏览器快捷键、后弹出截图”的干扰现象。
- **消息循环优化**: 为原生热键专门开辟了基于 `GetMessageW` 的阻塞式消息监听线程，实现 0% 额外 CPU 占用率。

## [V82.0] - 2026-04-02 (Memory Bridge & Smoothness)
### Fixed
- **剪贴板类型崩溃**: 修复了 PyQt6 环境下 `save()` 函数拒绝 Python `BytesIO` 对象的类型冲突报错。
- **QBuffer 桥接**: 引入 `QBuffer` + `QIODevice` 作为内存中转层，确保图像数据从 Qt 引擎平滑传递给 PIL 库。
- **打包依赖补全**: 针对 PyInstaller 可能漏掉 PIL 底层 C 引擎（`_imaging`）的问题，在打包脚本中强制锁定依赖。

## [V81.0] - 2026-03-30 (Smart UI & Tray Persistence)
### Added
- **工具栏“智能反弹”算法**: 重写了 `show_toolbar` 的坐标计算逻辑。程序会自动检测屏幕底部边界，当截图选区靠近底端时，工具栏会自动“跳跃”至选区上方弹出，防止 UI 溢出屏幕不可见。
- **托盘图标长驻机制**: 修复了任务栏图标运行数小时后随机消失的问题。通过在主线程入口建立 `tray_icon_ref` 全局强引用，防止其被 Python 垃圾回收机制 (GC) 错误回收。

## [V80.0] - 2026-03-24 (DPI Clean Surgery)
### Fixed
- **DPI 拒绝访问告警**: 彻底物理移除代码中所有手动调用的 `ctypes` DPI 设置语句。
- **引擎接管**: 发现 `uiautomation` 库与手动 DPI 声明存在时序冲突，改为完全信任 PyQt6 原生的 `Per-Monitor V2` 感知策略，回归最纯净的 Windows 窗口映射规则。
### Changed
- **日志净化**: 配合 `QT_LOGGING_RULES` 环境变量，物理静音了控制台关于 DPI 重复声明的非致命警告信息。

## [V77.0] - 2026-02-26 (The Black Box)
### Added
- **全域崩溃拦截网 (Black Box)**: 
  - 挂载 `sys.excepthook` 拦截主线程致命异常。
  - 挂载 `threading.excepthook` 捕捉后台守护线程的静默死亡。
- **可视化报警**: 发生未处理崩溃时，自动弹出带 Windows 原生红叉图标的对话框，指引用户前往查看 `debug.log`。
### Changed
- **日志标准**: 统一了 AppData 目录下 `debug.log` 的记录标准，确保每一次崩溃都有迹可循。

## [V76.0] - 2026-02-24 (System-Level Hard Restart)
### Fixed
- **睡眠死机终极修复 (方案A)**: 彻底解决在极端深度休眠 (S4) 场景下，由于输入队列挂起导致的快捷键永久失效问题。
- **系统级强力重启 (Hard Restart)**: 弃用了 V75 的内存重载方案。引入看门狗侦测时间跳变后，直接调用 `os.startfile` 启动新进程并让旧进程瞬间湮灭，确保 100% 干净的热键抢占。

## [V75.0] - 2026-02-21 (Micro-Surgery & Sleep Immunity)
### Fixed
- **睡眠断连修复**: 彻底解决系统休眠唤醒后热键失效。
- **鼠标监听不死化**: 为 `pynput` 监听线程引入“不死图腾”循环，崩溃后 2 秒内原地重启。
### Changed
- **架构回滚**: 恢复所有重型库的全局前置导入，杜绝单文件打包环境下的运行异常。

## [V72.0] - 2026-02-20 (Clipboard Ultimate Fix)
### Fixed
- **剪贴板为空**: 彻底修复 V66 之后数据结构截断导致的“无法粘贴”问题。
- **PIL 中转层**: 强制引入 PIL 作为图像中转，精准剥离 BMP 文件头后写入剪贴板 (`CF_DIB`)。

## [V66] - 2026-02-17 (Cross-Screen Capture)
### Added
- **跨屏幕截图**: 支持在多个显示器之间跨屏拖拽选区，实现虚拟画布拼接。

## [V65.0] - 2026-02-16 (Fixed Clipboard & HD Capture)
- **可靠性增强**: 改用 `win32clipboard` 直接写入 DIB 格式。

## [V64.0] - 2026-02-16 (Async Save & HD Capture)
- **异步保存**: 引入线程池处理截图保存，窗口响应零延迟。

## [V63.0] - 2026-02-16 (Persistent Config)
- **配置持久化**: 自动保存画笔颜色、字号至 `config.json`。

## [V61.0] - 2026-02-15 (Heartbeat Watchdog)
- **心跳看门狗**: 引入主动时间检测线程，通过 5 秒一次的物理时间校对判定系统睡眠。

## [V60.0] - 2026-02-07 (Auto-Wake Final)
- **智能唤醒**: 监听 `WM_POWERBROADCAST` 电源广播，实现无感复活。

## [V53.0] - 2026-01-16 (High-DPI Fix)
- **缩放修复**: 解决 4K 屏选区错位，改为手动计算物理像素缩放因子。

## [V41.0] - 2026-01-13 (UI Overhaul)
- **标注工具栏**: 新增矩形、圆形、箭头、画笔、撤销功能。
- **屏幕定格**: 截图触发瞬间画面静止，提供稳定画布。

## [V22.0] - 2026-01-02
- **框架迁移**: GUI 框架从 `tkinter` 全面迁移至 `PyQt6`。

## [V1.0] - 2025-12-20
- **项目初始化**: 基础鼠标监听，实现资源管理器双击返回。