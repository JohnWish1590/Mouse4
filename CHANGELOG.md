# Changelog

All notable changes to the **Mouse4** project will be documented in this file.

## [V47.0] - 2026-01-13 (Latest)
### Fixed
- **UI Bug**: 修复了工具栏分割线变量名引用错误导致的程序闪退问题 (Critical Hotfix)。
- **交互优化**: 移除文字输入框的默认占位符，点击屏幕即显示空白光标，不再出现默认字符。

### Changed
- **UI 细节**: 工具栏分隔符从字符 `|` 升级为专业的垂直分割线 (`QFrame`)，视觉更加整洁。

## [V46.0] - 2026-01-13
### Changed
- **UI 适配**: 加宽字号下拉框宽度，解决大字号数字显示不全的问题。
- **图标美化**: 字号选择器右侧图标替换为自定义的 SVG 上下箭头 (⇵) 样式，更具现代感。

## [V45.0] - 2026-01-13
### Fixed
- **Crash Fix**: 补全缺失的 `show_toolbar` 定位函数，修复截图完成时的崩溃问题。

### Added
- **功能增强**: 文字工具升级为下拉菜单选择，支持 12px-72px 多档字号，且支持实时预览调整。

## [V42.0] - 2026-01-13
### Added
- **核心升级**: 实现“原地文字输入” (Overlay Input)，点击屏幕直接出现透明输入框，所见即所得，回车确认。

### Changed
- **UI 重塑**: 工具栏全面升级为深色磨砂质感，图标尺寸加大，颜色选择器增加选中光圈特效。

### Fixed
- **Bug 修复**: 彻底解决箭头工具计算坐标时的类型错误 (`TypeError`) 崩溃问题。

## [V41.0] - 2026-01-13
### Added
- **核心重构**: 引入“屏幕定格”机制，截图触发瞬间画面静止，提供稳定的绘图画布。
- **新增工具**: 新增悬浮标注工具栏，包含矩形 (⬜)、圆形 (⭕)、箭头 (↗)、画笔 (✎) 及撤销 (↶) 功能。
- **体验优化**: 支持右键单击取消当前选中的绘图工具，再次右键退出截图。

---

## [V40.0] - 2026-01-05
### Added
- **[span_0](start_span)UI 美化**: 新增自动圆角裁剪算法[span_0](end_span)。
- **[span_1](start_span)图标优化**: 实现 `logo.ico` 在托盘显示时自动变为圆形，且支持打包命令将图标内置[span_1](end_span)。

## [V39.0]
### Fixed
- **[span_2](start_span)高清修复**: 引入像素密度比 (DPR) 计算，修复 2K/4K 高分屏缩放下截图尺寸偏小的问题[span_2](end_span)。
- **[span_3](start_span)层级修复**: 截图窗口改为 `showFullScreen`，强制覆盖任务栏，解决无法截取任务栏的问题[span_3](end_span)。

## [V38.0]
### Removed
- **[span_4](start_span)极简版**: 移除“设置双击速度”功能及菜单入口[span_4](end_span)。
- **[span_5](start_span)菜单精简**: 托盘菜单仅保留：GitHub、右键管理、退出[span_5](end_span)。

## [V37.0]
### Changed
- **[span_6](start_span)功能调整**: 移除热键设置功能，截图热键固定为 `Ctrl+1`[span_6](end_span)。

## [V36.0]
### Added
- **[span_7](start_span)尝试**: 新增按键录制窗口（*后因需求变更撤销*）[span_7](end_span)。

## [V35.0]
### Fixed
- **[span_8](start_span)打包修复**: 增加 `resource_path` 资源定位函数[span_8](end_span)。
- **[span_9](start_span)Bug 修复**: 解决打包为单文件 (`-F`) 后，托盘图标无法读取导致显示默认图标的问题[span_9](end_span)。

## [V34.0]
### Fixed
- **[span_10](start_span)核心修复**: 重写 `RegistryManager`，增加 EXE 环境判断 (`sys.frozen`)[span_10](end_span)。
- **[span_11](start_span)Bug 修复**: 解决打包后右键菜单找不到程序路径导致功能失效的问题[span_11](end_span)。

## [V33.0]
### Changed
- **[span_12](start_span)文案修正**: 统一菜单术语（“设置截图热键”、“设置返回上一层文件夹双击速度”）[span_12](end_span)。

## [V32.0]
### Added
- **[span_13](start_span)新增**: 托盘菜单增加“访问 GitHub 主页”选项[span_13](end_span)。
- **[span_14](start_span)依赖**: 引入 `webbrowser` 模块[span_14](end_span)。

## [V31.0]
### Changed
- **[span_15](start_span)体验优化**: 移除右键存图成功后的弹窗提示，实现“静默保存”[span_15](end_span)。

## [V30.0]
### Added
- **[span_16](start_span)功能找回**: 恢复丢失的“设置双击速度”功能及托盘入口[span_16](end_span)。
### Changed
- **[span_17](start_span)优化**: 优化托盘菜单结构[span_17](end_span)。

## [V29.0]
### Fixed
- **[span_18](start_span)基准修复**: 修复注册表写入权限问题，解决右键菜单偶尔失效的 Bug[span_18](end_span)。

---

## 早期版本 (Early Access)

### [V25.0 - V28.0]
- **[span_19](start_span)功能完善**: 完善右键菜单逻辑，增加 `--paste` 启动参数[span_19](end_span)。
- **[span_20](start_span)调试**: 增加诊断弹窗（用于调试剪贴板读取失败等问题）[span_20](end_span)。

### [V22.0]
- **[span_21](start_span)框架重构**: GUI 框架从 `tkinter`/`pystray` 全面迁移至 **PyQt6**[span_21](end_span)。
- **[span_22](start_span)UI**: 界面美化，增加半透明遮罩效果[span_22](end_span)。

### [V20.0]
- **[span_23](start_span)新增功能**: 初步尝试“右键菜单”集成[span_23](end_span)。
- **[span_24](start_span)核心**: 编写注册表写入逻辑，支持右键调用脚本[span_24](end_span)。

### [V15.0]
- **[span_25](start_span)核心升级**: 截图引擎从 `PIL` 迁移至 `mss`，支持多显示器截图[span_25](end_span)。

### [V11.0 - V14.0]
- **[span_26](start_span)新增功能**: 集成截图模块[span_26](end_span)。
- **[span_27](start_span)支持**: 添加默认截图快捷键支持[span_27](end_span)。

### [V10.0]
- **[span_28](start_span)UI 重构**: 移除 CMD 黑框运行模式[span_28](end_span)。
- **[span_29](start_span)核心**: 加入系统托盘图标（Tray Icon），程序最小化到后台运行[span_29](end_span)。

### [V5.0 - V9.0]
- **[span_30](start_span)智能识别**: 引入 `UIAutomation` 库，实现“空白处”智能识别，防止双击文件时触发返回[span_30](end_span)。
- **[span_31](start_span)配置**: 增加 `config.json` 配置文件支持[span_31](end_span)。

### [V2.0 - V4.0]
- **[span_32](start_span)优化**: 优化双击判定逻辑，解决单击误触问题[span_32](end_span)。
- **[span_33](start_span)限制**: 引入 `is_explorer_window` 判断，限制仅在资源管理器生效[span_33](end_span)。

### [V1.0]
- **[span_34](start_span)项目初始化**[span_34](end_span)。
- **[span_35](start_span)基础功能**: 监听鼠标左键双击[span_35](end_span)。
- **[span_36](start_span)核心逻辑**: 发送 `Alt+Up` 模拟返回上一级[span_36](end_span)。
