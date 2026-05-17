# Changelog

All notable changes to the Mouse4 project will be documented in this file.

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