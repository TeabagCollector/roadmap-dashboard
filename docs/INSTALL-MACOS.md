# Install Dashboard for Codex / 安装说明

Apple silicon (M1 or newer), macOS 15+ deployment target. Version **0.5.0-preview.5** includes Python; no extra login, API key or developer tools are needed.

## Three steps

1. **Download the DMG** from the [test release](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.5). Choose the `.dmg`; the application ZIP is an alternative and the source ZIP is for developers.
2. **Drag Dashboard for Codex.app into Applications.** Eject the disk image and open the installed app. You can also use your own `~/Applications` folder. Quit a previous copy before replacing it.
3. **Click Start tracking real work** when your local Codex records are found. Leave **Also enable roadmap tracking** selected to install the separate sync skill, or uncheck it for conversation monitoring alone. Missing sources are explained with retry and folder selection. In a new supported Codex work chat, give the agent a concrete task; an existing chat can invoke `$roadmap-dashboard-sync` once.

## If macOS blocks opening

This test app is ad-hoc signed and **not notarized**. If you trust the source and choose to proceed, use the per-app **Open Anyway** option in System Settings → Privacy & Security when offered. If it is reported as damaged or the option is unavailable, report the message. Keep system-wide security enabled.

## Roadmap display

Use **Sort** beside **My roadmap** to reveal drag handles and up/down arrows; click **Done sorting** to finish. **View** contains compact overview, hiding completed steps, and the per-task step limit (3 / 5 / 8 / all). Longer roadmaps have a button to show the remaining steps. Use ⌘F or the search button to find a task or project; Escape clears the search. ⌘, opens view settings, including small / standard / large text. Search terms stay in memory and ordering is disabled while a query filters the list. View settings and order persist without changing task records.

## Optional checksum check

`SHA256SUMS.txt` is available if you want to verify download integrity. **It is optional and is not part of the normal installation steps.** It does not replace application signing or notarization.

## Feedback and removal

Another physical Mac and macOS 15 itself remain unverified. For testing, report chip type, macOS version, whether opening worked, and any error. You do not need to send personal information or real chats. Try language switching, display options and quitting/reopening; connecting local work is your choice.

To remove the app, quit it and move the app to Trash. Tasks and preferences remain in `~/Library/Application Support/RoadmapDashboardPreview`; an explicitly installed sync skill also remains. If you move or reinstall the app, reinstall the skill from setup so its local client follows the app's location. [Connection guide](https://github.com/TeabagCollector/roadmap-dashboard/blob/main/docs/CONNECT.md).

---

## 中文：三步安装

适用于 M1 或更新芯片的 Mac，部署目标为 macOS 15+。自带 Python，不需要另行登录、API Key 或开发工具。

1. **下载 DMG**：[打开测试版下载页](https://github.com/TeabagCollector/roadmap-dashboard/releases/tag/v0.5.0-preview.5)，选择 `.dmg` 即可。
2. **拖入 Applications**：复制应用后推出镜像，再从 Applications 打开；也可以放自己的 `~/Applications`。更新前先退出旧版。
3. **点“开始追踪真实工作”**：检测到本机 Codex 记录后确认接入。同屏可一起启用任务路线同步 skill；已有对话可调用一次 `$roadmap-dashboard-sync`，新工作对话可发现该 skill。找不到来源时按提示重试或选文件夹。

尚未公证，macOS 可能拦截。如果信任来源并决定继续，可在系统提供时使用“系统设置 → 隐私与安全性 → 仍要打开”单独授权；若提示损坏或无相应选项，反馈提示即可，不关闭系统安全保护。

**清单显示：** “我的清单”旁的 **排序** 直接显示把手和上下按钮；点“完成排序”退出。“显示”菜单提供紧凑概览、隐藏已完成步骤，以及 3 / 5 / 8 / 不限的条数选择，长路线可展开剩余步骤。⌘F 或搜索按钮可找任务/项目，Esc 退出；⌘, 打开显示设置，另有三档文字大小。搜索词只在内存中保留，搜索时暂不排序。设置与顺序会保存，不改任务记录。

**SHA256 校验完全可选，普通安装不需要做。** 校验文件留给需要检查下载完整性的人。

第二台真实 Mac 和 macOS 15 本身仍待验证。试用反馈只需芯片、系统版本、是否能打开和报错。卸载时退出并移走应用，原清单和偏好保留；移动或重装应用后，可在设置中重新安装同步 skill。

## Show / hide and updates / 唤起隐藏与更新

On first launch, choose **Enable ⌘D** to register a global shortcut while Dashboard is running. Press once to bring the panel forward; press again when active to hide it. **Not Now** keeps it off, and your choice survives restarts. This uses ⌘D across applications, replacing their normal action while enabled. No Accessibility permission is needed. The menu-bar icon always offers **Show / Hide Dashboard**, **Enable ⌘D Global Shortcut**, and **Check for Updates…**.

If another application or a second Dashboard copy holds ⌘D, an alert and menu status explain the conflict. Release it in that application, then choose **Retry ⌘D**. The app does not silently take it over.

**Check for Updates…** opens the GitHub releases page only when clicked. Download the new DMG, quit Dashboard, replace the application, then reopen it. Your existing roadmap, themes, language and shortcut choice are stored separately and retained. This is a manual update shortcut, not background checking or automatic replacement. Older builds without this menu need one manual download first.

首次启动选择 **开启 ⌘D**，应用运行时即可全局唤起；面板已激活时再按一次隐藏。选择 **暂不开启** 则不占用快捷键，两种选择都会记住。开启期间会替代其他应用原有的 ⌘D 功能，可从顶部菜单栏的 Dashboard 图标随时开关，无需辅助功能权限。

如其他应用或另一份 Dashboard 已占用快捷键，会弹出提示并在菜单显示状态；释放占用后，选择 **重试 ⌘D**。菜单始终提供 **显示 / 隐藏 Dashboard** 作为替代。

**检查更新…** 仅在点击时打开 GitHub 下载页，不后台检查或自动替换。下载新版 DMG，退出旧应用后替换，再打开即可。原有清单、主题、语言和快捷键选择保留。旧版没有此入口的用户，需要先手动下载升级一次。
