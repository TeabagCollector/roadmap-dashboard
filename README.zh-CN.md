# Dashboard for Codex

An independent macOS companion for local work in ChatGPT Desktop.

**把对话放在眼前，让每个任务都有路线。**

为 macOS 上的 ChatGPT Desktop 本机工作设计的独立伴随面板：跨项目看对话、留意新回复，把任务展开成可以逐步核验的清单。

[**下载 macOS 测试版**](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.5) · [English](README.md) · [三步入门](#三步入门) · [完整接入指南](docs/CONNECT.md) · [数据读写](docs/PRIVACY.md)

<a href="docs/preview-zh.png"><img src="docs/preview-zh.png" alt="Dashboard for Codex 中文暖纸主题：工作对话与可展开路线清单" width="340"></a>

## 看它如何工作

<a href="docs/demo-zh.gif"><img src="docs/demo-zh.gif" alt="虚构样例短演示：回复返回、展开任务、上报待核验、手动勾选完成" width="360"></a>

约 14 秒的公开界面样例演示。对话事件和 agent 交付报告是模拟输入；展开任务和勾选步骤使用预览本身的真实控件。不展示任何真实对话或项目。[演示说明](docs/DEMO.md)。

## 三件事，一眼看清

- **对话：** 区分正在生成与已回复未读，生成期间保持顺序稳定，历史未读默认折叠。
- **路线：** 展开任务查看步骤、进度与证据，返回关联的本机工作对话。
- **完成：** agent 上报交付后仍待核验，验证或由你勾选后才算完成。保留手动完成与重新打开的选择。

对话区和清单区可拖动调整、独立滚动；支持五种主题和中英界面切换。“我的清单”旁直接点 **排序** 调整顺序，**显示** 可选紧凑概览、隐藏已完成步骤及 3 / 5 / 8 / 不限的条数，重启保留设置。支持 **⌘F** 本机任务/项目搜索、**⌘,** 显示设置和三档文字大小，搜索词不保存。[设计取舍与对比](docs/DESIGN.md)。普通安装只需下载 → 拖入 Applications → 打开接入，SHA256 校验可选。

首次启动可选择开启 **⌘D**，用于全局唤起或隐藏已激活的面板；顶部菜单栏图标可随时开关，快捷键冲突会明确提示并支持重试。同一菜单的 **检查更新…** 可打开下载页，手动替换新版会保留本机数据。

## 三步入门

**Apple silicon 应用测试预览：** [下载 v0.5.0-preview.5](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.5)。自带 Python，无需安装开发工具；**尚未公证**，首次打开可能被 macOS 拦截，第二台真实 Mac 仍待验证。请先阅读[安装与测试说明](docs/INSTALL-MACOS.md)。

如果选择**源码安装**，需要 macOS 15+、Swift 6 命令行工具和 Python 3.9+。

1. **安装。** [下载源码预览](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.5)，解压后运行 `Install.command`。只想先看看，可以在浏览器打开 `src/index.html`。
2. **开始追踪。** 首次打开会检测默认的本机 Codex 工作记录。找到后点“开始追踪真实工作”；保持勾选“同时启用任务路线同步”，可在同一次操作中安装独立同步 skill，不需要登录或 API Key。未找到时，先在 Codex 开一次本机工作对话，或选择正确的记录文件夹。
3. **照常开工。** 接入后就能读取已有本机对话状态。新开受支持的 Codex 工作对话、交付具体任务，让 agent 发现同步 skill；已打开的对话可调用一次 `$roadmap-dashboard-sync` 接入。路线由当前 agent 在计划、交付等节点维护，不把所有消息自动转成任务；已有清单仍可在设置中选 `ledger.json` 共享。

浏览器预览只使用虚构数据，不能接入真实文件。源码构建的应用和数据目录沿用 Roadmap Dashboard Preview 名称；预编译候选应用名为 Dashboard for Codex。依赖检查、手动未读、共享清单和卸载见[完整指南](docs/CONNECT.md)。

## 同步怎么实现

```mermaid
flowchart TD
    A[本机工作记录] -->|只读获取对话状态| C[Dashboard 面板]
    B[当前 agent + 可选同步 skill] -->|计划、交付与验收记录| D[本机路线清单]
    D --> C
    C -->|你手动勾选| D
```

对话状态来自本机记录；路线由当前处理任务的 agent 配合同步 skill 维护。仅安装面板不会自动把所有聊天变成任务。基础监测和清单同步不额外调用后台模型。

## 支持范围与版本状态

当前开发和验证针对 **ChatGPT Desktop 中基于本地 Codex 记录的工作／编程对话**。不连接 ChatGPT 账号，不获取普通云端聊天历史。中英切换不会翻译对话与任务正文。

这是独立项目，并非 OpenAI 官方产品。其他桌面客户端、远程主机及其他 agent 兼容性尚未验证；上游格式变化时，无法判断的活动会显示为未知。

源码预览已在一台 Apple silicon Mac 验证。本地构建应用采用临时签名，尚未公证；Intel 和第二台真实机器安装仍待验证。截图和演示均使用虚构样例。

## 开发与许可

```sh
bash build.sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/conversations.test.cjs
```

源码导出：`scripts/export_source.py`。另见[相关工具](docs/LANDSCAPE.md)。

采用 [MIT 许可](LICENSE)，Copyright © 2026 TeabagCollector。
