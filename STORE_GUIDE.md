# 发布 / 上架指南

> 针对「Mouse4」桌面截图工具。最后更新：2026-08-16
>
> ⚠️ **本期（v107.0）暂不上架任何应用商店**：当前通过 GitHub Releases 直接分发 exe。本指南为未来多渠道分发预留。

## 一、前置条件

- 一个 GitHub 账号
- 仓库已公开：`https://github.com/JohnWish1590/Mouse4`

## 二、准备发布包

1. 确保 `main.pyw` 版本号已更新。
2. 同步更新 `CHANGELOG.md`、`RELEASE_NOTE.md`、`README.md`。
3. 用 PyInstaller 构建两种产物：
   - `Mouse4_onefile.spec` → 单文件版
   - `Mouse4_onedir.spec` → 文件夹版
4. 在 GitHub Releases 上传构建产物。

## 三、Release 信息填写

| 字段 | 建议内容 |
|------|----------|
| 标题 | Mouse4 v107.0 |
| 描述 | 复制 `RELEASE_NOTE.md` 中对应版本内容 |
| 附件 | `Mouse4.exe`、`Mouse4_onedir.zip` |

## 四、作者信息

- **作者**：下一站澳门
- **邮箱**：cheung.cn@gmail.com
- **GitHub**：https://github.com/JohnWish1590/Mouse4
- **微博**：@下一站澳门
