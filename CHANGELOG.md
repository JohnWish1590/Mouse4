# Changelog

All notable changes to the Mouse4 project will be documented in this file.

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