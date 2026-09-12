<p align="center">
  <h1 align="center">📌 QuickMemo</h1>
  <p align="center">
    <strong>一款极致轻量、丝滑流畅的 Windows 桌面便签工具。</strong><br>
    <em>随手记，随心隐，让灵感与思绪不再丢失。</em>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square" alt="Python">
    <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg?style=flat-square" alt="PyQt5">
    <img src="https://img.shields.io/badge/Platform-Windows%2010/11-blue.svg?style=flat-square" alt="Platform">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License">
  </p>
</p>

---

## ✨ 核心特性

- 🚀 **秒开秒记**：全局快捷键 `Alt + M`，随时随地唤出/隐藏便签，不打断当前工作流。
- 🌊 **边缘滑出**：屏幕右侧边缘感应条，鼠标轻触，所有便签依次丝滑滑出（带阶梯式错位动画），离开自动隐藏。
- 🗒️ **多便签并存**：可同时开多张便签，新建时自动级联错位排布，互不遮挡。
- 🍃 **用完即走**：主打"无负担"记录——启动时自动清除上次会话残留，退出程序或系统关机时即清空全部便签数据，本地不长期保存任何内容，极致保护隐私。
- 📌 **自由置顶**：独立图钉按钮，重要事项永远置顶，不遮挡其他窗口。
- 🛡️ **单例运行**：基于本地 Socket（`127.0.0.1:65479`）的单例检测，多次点击 exe 不会重复打开，而是智能唤醒已有窗口；并带重试机制，覆盖开机自启冷启动的窗口期。
- 🌙 **静默自启**：一键设置开机静默启动（`--silent`，注册表 `HKCU\...\Run`），融入系统底层，无感陪伴。
- 🖥️ **托盘常驻**：系统托盘右键菜单——显示所有便签 / 新建便签 / 开机自启开关 / 退出程序。
- 🎨 **极简美学**：无边框设计 + 亚克力半透明质感，完美融入各类桌面壁纸；支持系统高 DPI 缩放，图标高清无噪点。

## 🚀 快速开始

### 1. 环境运行（开发者）

确保您的系统已安装 Python 3.8 及以上版本。

```bash
# 克隆项目
git clone https://github.com/xinghui79/QuickMemo.git
cd QuickMemo

# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py
```

### 2. 打包为 EXE（可选）

使用 PyInstaller 打包为单文件夹、无控制台窗口的绿色版程序：

```bash
pip install pyinstaller

pyinstaller --clean -y -D -w -n QuickMemo --icon=assets/icon.ico --add-data "assets;assets" main.py
```

打包产物位于 `dist/QuickMemo/`，双击其中的 `QuickMemo.exe` 即可运行。也可以直接前往 [Releases](https://github.com/xinghui79/QuickMemo/releases) 页面下载已打包好的版本。

## 📖 使用说明

| 操作 | 方式 |
| --- | --- |
| 唤出 / 隐藏所有便签 | 全局快捷键 `Alt + M`，或鼠标触碰屏幕右侧边缘感应条 |
| 新建便签 | 托盘右键菜单 →「新建便签」 |
| 置顶 / 取消置顶 | 点击标题栏 ▲ 图钉按钮 |
| 销毁便签 | 点击标题栏 ✕ 关闭按钮（即时销毁，不留痕迹） |
| 移动便签 | 按住标题栏拖动 |
| 开机自启 | 托盘右键菜单勾选「开机自动启动」 |
| 退出程序 | 托盘右键菜单 →「退出程序」（清空全部数据后退出） |

> ⚠️ QuickMemo 的设计哲学是"阅后即焚"：程序退出、便签销毁或系统关机后，本次会话记录的所有内容都会被彻底清除，请勿用它保存需要长期留存的资料。

## 🗂️ 项目结构

```
QuickMemo/
├── main.py               # 程序入口：单例检测、高 DPI 初始化、模块装配
├── core/
│   ├── tray_manager.py   # 全局托盘与窗口管理器：生命周期、滑出动画、会话数据清理
│   ├── hotkey.py         # 全局热键 (Alt + M) 注册与响应
│   ├── server.py         # 本地 Socket 服务，用于单例唤醒
│   ├── autostart.py      # 开机自启（注册表读写）
│   └── ...
├── ui/
│   ├── memo_window.py    # 便签窗口：置顶、拖动、销毁、数据暂存
│   └── edge_sensor.py    # 屏幕右缘感应条
├── assets/
│   └── icon.ico          # 应用图标
└── QuickMemo.spec        # PyInstaller 打包配置
```

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。
