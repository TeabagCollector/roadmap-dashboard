# macOS app preview / macOS 应用预览

## Candidate status

Version: **0.5.0-preview.1**, Apple silicon only, macOS 15+ deployment target. The candidate includes CPython 3.12.16 and requires no separate Python, Swift, API key or account. It is locally ad-hoc signed and **not notarized**. One physical Apple silicon Mac has been tested; another Mac and macOS 15 have not been tested. This is a test candidate, not a verified general release.

## Install

1. Open the disk image and copy **Dashboard for Codex.app** to Applications, or to your own `~/Applications` folder if you prefer a user-local installation. Quit any previous copy before replacing it. Keep your existing copy as a backup when testing an update.
2. Eject the disk image, then open the installed application. The first launch should show a bilingual setup view and fictional sample tasks, without asking for an administrator password or developer tools.
3. Choose **Connect local ChatGPT Desktop work records** in setup. A supported local record source is required for real conversations. Optionally install the roadmap skill for your coding agent. Follow [the connection guide](CONNECT.md) for manual unread and shared roadmaps.

macOS may block an application downloaded from the internet because this preview is not notarized. If you trust its source and choose to proceed, use the per-application **Open Anyway** option in System Settings → Privacy & Security, when macOS offers it. Do not disable Gatekeeper, remove quarantine recursively, or change system-wide security settings. If the application is reported as damaged or a required option is unavailable, stop and report the exact message.

## What to check on another Mac

- Record the macOS version and chip type; no need to send your name, hostname, file paths or chat contents.
- Confirm that the downloaded file's SHA256 matches `SHA256SUMS.txt`.
- Before installing developer tools or Python, check whether the application opens by itself; record the exact Gatekeeper behavior.
- Check that setup appears, English / Chinese switching works, sample tasks expand, and a sample check survives quitting and reopening.
- If you choose to connect real local work, confirm that missing sources are explained and conversation status is readable. Share only whether the check passed; do not send real chat titles, credentials, screenshots or ledgers.
- Quit the application. Move only the app to Trash to uninstall. Your roadmap and connection settings should remain.

## Data and removal

The default data folder remains `~/Library/Application Support/RoadmapDashboardPreview` for compatibility. The candidate does not automatically import other projects or install a hook. Removing the app leaves tasks, preferences and an explicitly installed roadmap skill in place. The skill's local client needs the app; reinstall it and reselect the skill in setup after moving the app. See [data handling](PRIVACY.md).

---

## 中文

这是 **0.5.0-preview.1** Apple silicon 候选包，部署目标为 macOS 15+，自带 Python，不要求使用者另装 Swift 或 Python，也不要求 API Key 或新账号。已做本地临时签名，尚未公证；目前只有一台真实 Mac 的测试结果，不能据此宣称其他机器或 macOS 15 已验证。

安装：打开 DMG → 把应用复制到 Applications（也可放自己的 `~/Applications`）→ 推出 DMG 后从安装位置打开。首次显示设置页和虚构样例，再自行选择是否接入本机工作记录。更新前退出旧版并保留备份。

下载的未公证应用可能被 macOS 拦截。如果你信任来源并决定继续，可在系统提供时使用“系统设置 → 隐私与安全性 → 仍要打开”对这一款应用单独授权。不关闭 Gatekeeper，不批量清除隔离标记，不修改系统安全策略；若显示已损坏或没有相应选项，停止并记录提示。

第二台测试只需返回芯片、系统版本、是否安装成功和错误提示，无需发送姓名、主机名、路径、真实对话、截图或清单。先在没安装 Python/开发工具的情况下试启动，再检查语言、展开/勾选、退出重开和自愿接入。卸载时仅移走应用，清单和偏好应保留；可选 skill 仍保留，但需要应用支持，重新安装或移动应用后应在设置中重新安装该 skill。
