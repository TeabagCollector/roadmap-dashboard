# Install and connect / 安装与接入

## English

1. **Check prerequisites.** Source installation needs macOS 15+, Swift 6 command-line tools and Python 3.9+. No administrator password, API key or new account is needed by this app. It does not download tools. Run `python3 scripts/install.py --dry-run` to inspect the destination and detected Python without installing.
2. **Install locally.** Run `Install.command`, or `python3 scripts/install.py`. The app goes to your own `~/Applications` directory; data remains in Application Support. A known earlier installation is preserved as `.previous` during an update. Unknown apps are not overwritten. Quit this preview before replacing it. A locally built app is ad-hoc signed, not notarized.
3. **Connect conversations.** Open the app's gear button, then **Connect local ChatGPT Desktop work records**. The app verifies the source read-only before changing the connection. If the local work-data folder differs from the default, use **Choose another Codex folder**. Missing or unsupported sources are explained rather than treated as an empty successful connection. The app never reads auth files or starts a model.
4. **Choose the roadmap.** A new installation starts with an independent ledger. Choose **Share an existing roadmap** and select an existing `ledger.json` if you already have a Dashboard. This shares the actual file, not a one-time copy. Both panels and the installed agent client then follow the same revisioned ledger. Manual checks/reopen decisions persist. Other project bridges, model settings and account bindings are not imported. Changing to a separate roadmap retains the old one.
5. **Optionally connect your coding agent.** Click **Install roadmap skill**. A separate `roadmap-dashboard-sync` skill is installed only in the selected local work-data folder. Existing unowned skills are never overwritten; existing skills, global AGENTS files and hooks are untouched. A private local client follows the current app connection each time, so reconnecting does not leave an agent writing an old ledger. Start a new chat to discover the skill, or invoke it explicitly. It guides substantive authorized plans/deliveries; it does not enroll casual questions. Automatic selection depends on the agent's skill support and is not a new background model.
6. **Optionally connect manual unread.** Pick a read chat, click **Start unread check**, mark that exact chat unread in ChatGPT Desktop, and click **Verify my unread mark**. A unique observed local identity/host transition is required; no credential-based identity guessing is used. If there is no unique change, the binding is not created. The app never marks the source chat itself. Re-verify after switching desktop accounts.

The app opens the setup view on a new profile. English and Chinese switching also applies to setup and native menus. Browser preview shows the flow but cannot connect real files. The app's global shortcut is not enabled by default, so shortcut conflicts are avoided.

### Disconnect, diagnostics and removal

Disconnect returns the panel to fictional demo data and retains all real ledgers and settings. A disconnected agent client refuses writes instead of falling back to the demo. Sharing another ledger resets the panel's data context, even if the new ledger's revision is lower; demo records are not carried into real work.

`python3 scripts/install.py --uninstall` removes only the app identified by its installation receipt. Data and installed skills are preserved. To undo agent enrollment, remove only the `roadmap-dashboard-sync` folder that this setup installed after inspecting it; there is no automatic hook to remove. Reinstall the app before using its local client again. No broad cache or user-data deletion is performed.

Advanced paths: installer `--apps-dir` and `--base` select a custom app/profile location. Launch a custom-profile app with `--base <directory>`. `--data` is reserved for isolated demo/QA runs. The direct client supports `status` and JSON `request`; it allows get/plan/report/accept and rejects the UI-only check operation.

This flow was checked with isolated source fixtures, a shared ledger, an installer sandbox and local real-source reads on one Apple silicon Mac. It does not establish cross-machine compatibility, notarization or support for ordinary ChatGPT, remote hosts or other agent runtimes.

## 中文

1. 安装前需要 macOS 15+、Swift 6 命令行工具和 Python 3.9+。运行 `python3 scripts/install.py --dry-run` 先看依赖与目标目录；程序不自动下载工具，不要求 API Key 或新账号。
2. 双击 `Install.command` 或运行安装脚本，安装到自己的 Applications 目录，不需要管理员权限。更新时保留已识别的旧版本；遇到同名未知应用会停止，不覆盖它。卸载只移除有本应用安装回执的程序，保留清单、连接设置与用户数据。
3. 打开面板右上角齿轮，点“连接ChatGPT Desktop 本机工作记录”。只读检查来源通过后才保存接入；路径不同时使用文件夹选择器。不是登录流程，不调用模型。
4. 初次接入会建立独立清单。已有清单可选“使用已有清单”，选择对应的 ledger.json；两个面板和同步入口将维护同一文件，后续更新会持续联通。原目录保留，不复制项目桥、模型配置或身份绑定。用户手动勾选优先，不把已上报等同于已验收。
5. 可选安装 `roadmap-dashboard-sync` skill，名称独立，不覆盖原有同步 skill、AGENTS 或 hook。新对话可发现它，也可明确调用。真正工作开始、计划变化、交付和验收时更新，不将闲聊逐条建任务；使用的仍是当前对话模型，不增加常驻模型。
6. 手动未读可选核验：选一段已读对话→开始检查→到 ChatGPT Desktop 将这段对话标为未读→返回核验。只有唯一且明确的本机身份变化才绑定；不读取凭据，不由面板替你改源对话。切换账号后重做核验。

中英切换同时覆盖接入页和菜单。断开接入会回到演示，不删除真实清单；断开时 agent 客户端拒绝写入，不会误写到演示清单。浏览器版只预览流程，真实接入使用原生应用。当前只在本机 Apple silicon 环境验收，正式分发、公证与其他机器兼容性仍需单列验证。
