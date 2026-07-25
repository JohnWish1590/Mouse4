🎯 Mouse4 V103.0 - 稳定性持续加固版

本次更新修复了两个运行时崩溃：截图白屏崩溃（快捷键触发后屏幕全白然后程序退出）和箭头标注类型错误。同时增加了 30 天日志自动裁剪功能。

✨ 核心亮点

📸 截图白屏崩溃已修复
按下截图快捷键后屏幕全白然后程序退出的问题已解决。根因是 `SnippingWindow` 构造函数中 `showFullScreen()` 在所有属性初始化之前调用，Qt 立即触发 `paintEvent` 但 `full_screenshot` 属性尚不存在。现已将所有属性初始化移到 `showFullScreen()` 之前。

✏️ 箭头标注类型错误已修复
`draw_arrow` 中 `end` 是 `QPoint` 但与 `QPointF` 进行减法运算时报 `TypeError`。修复为函数入口统一转换为 `QPointF`。

🗑️ 30 天日志自动裁剪
`debug.log` 写入时自动清理超过 30 天的记录，`[FATAL CRASH]` 行永久保留。每天最多执行一次，无性能开销。解决 AppData 目录日志长期累积问题。

🐛 修复列表
- 修复 截图快捷键后白屏崩溃（`full_screenshot` 初始化时序）
- 修复 箭头标注 `QPoint` 与 `QPointF` 类型错误崩溃
- 修复 日志文件无限增长（30 天自动裁剪）
