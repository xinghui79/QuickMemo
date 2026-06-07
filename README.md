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
- 🌊 **边缘滑出**：独创屏幕右侧边缘感应条，鼠标轻触，便签丝滑滑出，离开自动隐藏。
- 🍃 **阅后即焚**：主打“无负担”记录，销毁便签或退出程序即清空，本地不产生任何缓存文件，极致保护隐私。
- 📌 **自由置顶**：独立图钉按钮，重要事项永远置顶，不遮挡其他窗口。
- 🛡️ **单例运行**：基于 Socket 的单例检测，多次点击 exe 不会重复打开，而是智能唤醒已有窗口。
- ⚙️ **开机自启**：一键设置开机静默启动（`--silent`），融入系统底层，无感陪伴。
- 🎨 **极简美学**：无边框设计 + 亚克力半透明质感，完美融入各类桌面壁纸。

---

## 🚀 快速开始

### 1. 环境运行 (开发者)

确保您的系统已安装 Python 3.8 及以上版本。

```bash
# 克隆项目
git clone https://github.com/xinghui79/QuickMemo.git
cd QuickMemo

# 安装依赖
pip install -r requirements.txt

# 启动应用
python main.py