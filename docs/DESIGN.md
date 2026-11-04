# Design notes: a focused desktop companion

This comparison uses official product documentation checked on 2026-11-05. The examples are established desktop utilities, extension platforms and focused apps; this is not an objective industry ranking or a hands-on benchmark. No competitor code, screenshots or visual assets are incorporated.

| Product / author | Characteristic documented by the product | Useful lesson for Dashboard | Decision in this preview |
| --- | --- | --- | --- |
| [Raycast — Settings](https://manual.raycast.com/settings) | Searchable settings, familiar keyboard access, appearance and shortcut controls | Let people find things without remembering where every option lives | Add a visible roadmap search button plus ⌘F; ⌘, opens nearby view settings |
| [Alfred — File Search](https://www.alfredapp.com/help/features/file-search/) | Essential default results, with explicit ways to widen the search scope | Keep quick search predictable and bounded | Search task titles and project labels already in the local ledger; no system-wide scan or model query |
| [Rectangle — rxhanson](https://github.com/rxhanson/Rectangle) | Keyboard and mouse actions with configurable shortcut behavior and app-specific exceptions | Input should be deliberate and tested at the actual native event boundary | Keep button/keyboard ordering and use pointer capture for dragging; validate native-window mouse input, release and cancellation |
| [Dato — Sindre Sorhus](https://sindresorhus.com/dato) | A compact menu-bar calendar with adaptable settings and documented use cases | Offer flexibility through small preferences without expanding the default surface | Add small / standard / large text in View; keep the American Typewriter title and compact default panel |
| [CodexBar — steipete](https://github.com/steipete/CodexBar) | A compact companion for provider limits, usage and status, with provider-specific source setup | A companion should make its source and limitations understandable | Keep real-work onboarding explicit, distinguish working from unread, and document which local conversations are supported |
| [Obsidian — Quick switcher](https://help.obsidian.md/plugins/quick-switcher) | Keyboard invocation, name matching and navigation to existing notes | Quick access is more useful when it preserves the existing organization | Search does not rewrite manual order or create tasks; clearing search returns to the same roadmap |

## Scope of the improvements

The task search is local, matches task names and project labels, and keeps its query only in memory. It does not inspect conversation content, search files, call a model, or write search history. Ordering is disabled while a non-empty query filters the list, so arranging a subset cannot unexpectedly move hidden tasks.

Text size changes conversation and task content, not the window title. A task title has the same size when collapsed and expanded. The choice is saved locally with view preferences.

Motion serves continuity: tasks reveal content with an interpolated height, following rows move with the disclosure, and pointer dragging previews a placement before committing it. Escape cancels a drag. Reduced-motion preferences skip nonessential animation.

These decisions keep the companion focused on existing work and roadmaps. They do not add a cloud account, background model loop, unrelated integrations, a full command platform, or system-wide search. Signing/notarization and another physical Mac remain separate release limitations.

## 中文摘要

参考的是成熟工具的交互原则，而非复制外观：Raycast 的可发现入口、Alfred 的明确搜索范围、Rectangle 的输入行为、Dato 的小而灵活、CodexBar 的来源说明，以及 Obsidian 的键盘快速访问。

本轮落实为：⌘F 搜索本机清单中的任务与项目、⌘, 打开显示设置、三档文字大小，以及真实指针拖动和展开过渡修复。搜索词不保存、不调模型；搜索不会改变人工顺序或创建任务。保留现有轻量面板、中文、主题与用户完成决定。
