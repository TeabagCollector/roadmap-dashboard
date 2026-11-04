# Install Dashboard for Codex / 安装说明

Apple silicon (M1 or newer), macOS 15+ deployment target. Version **0.5.0-preview.3** includes Python; no extra login, API key or developer tools are needed.

## Three steps

1. **Download the DMG** from the [test release](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.3). Choose the `.dmg`; the application ZIP is an alternative and the source ZIP is for developers.
2. **Drag Dashboard for Codex.app into Applications.** Eject the disk image and open the installed app. You can also use your own `~/Applications` folder. Quit a previous copy before replacing it.
3. **Click Start tracking real work** when your local Codex records are found. Leave **Also enable roadmap tracking** selected to install the separate sync skill, or uncheck it for conversation monitoring alone. Missing sources are explained with retry and folder selection. In a new supported Codex work chat, give the agent a concrete task; an existing chat can invoke `$roadmap-dashboard-sync` once.

## If macOS blocks opening

This test app is ad-hoc signed and **not notarized**. If you trust the source and choose to proceed, use the per-app **Open Anyway** option in System Settings → Privacy & Security when offered. If it is reported as damaged or the option is unavailable, report the message. Keep system-wide security enabled.

## Roadmap display

Use **Sort** beside **My roadmap** to reveal drag handles and up/down arrows; click **Done sorting** to finish. **View** contains compact overview, hiding completed steps, and the per-task step limit (3 / 5 / 8 / all). Longer roadmaps have a button to show the remaining steps. View settings and order persist without changing task records.

## Optional checksum check

`SHA256SUMS.txt` is available if you want to verify download integrity. **It is optional and is not part of the normal installation steps.** It does not replace application signing or notarization.

## Feedback and removal

Another physical Mac and macOS 15 itself remain unverified. For testing, report chip type, macOS version, whether opening worked, and any error. You do not need to send personal information or real chats. Try language switching, display options and quitting/reopening; connecting local work is your choice.

To remove the app, quit it and move the app to Trash. Tasks and preferences remain in `~/Library/Application Support/RoadmapDashboardPreview`; an explicitly installed sync skill also remains. If you move or reinstall the app, reinstall the skill from setup so its local client follows the app's location. [Connection guide](https://github.com/TeabagCollector/roadmap-dashboard/blob/main/docs/CONNECT.md).

---

## 中文：三步安装

适用于 M1 或更新芯片的 Mac，部署目标为 macOS 15+。自带 Python，不需要另行登录、API Key 或开发工具。

1. **下载 DMG**：[打开测试版下载页](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.3)，选择 `.dmg` 即可。
2. **拖入 Applications**：复制应用后推出镜像，再从 Applications 打开；也可以放自己的 `~/Applications`。更新前先退出旧版。
3. **点“开始追踪真实工作”**：检测到本机 Codex 记录后确认接入。同屏可一起启用任务路线同步 skill；已有对话可调用一次 `$roadmap-dashboard-sync`，新工作对话可发现该 skill。找不到来源时按提示重试或选文件夹。

尚未公证，macOS 可能拦截。如果信任来源并决定继续，可在系统提供时使用“系统设置 → 隐私与安全性 → 仍要打开”单独授权；若提示损坏或无相应选项，反馈提示即可，不关闭系统安全保护。

**清单显示：** “我的清单”旁的 **排序** 直接显示把手和上下按钮；点“完成排序”退出。“显示”菜单提供紧凑概览、隐藏已完成步骤，以及 3 / 5 / 8 / 不限的条数选择，长路线可展开剩余步骤。设置与顺序会保存，不改任务记录。

**SHA256 校验完全可选，普通安装不需要做。** 校验文件留给需要检查下载完整性的人。

第二台真实 Mac 和 macOS 15 本身仍待验证。试用反馈只需芯片、系统版本、是否能打开和报错。卸载时退出并移走应用，原清单和偏好保留；移动或重装应用后，可在设置中重新安装同步 skill。
