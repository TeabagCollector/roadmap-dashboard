# Data handling

## Demo mode

The browser and native demo use bundled fictional examples. Browser preferences are stored in local storage. The native demo keeps its own checklist and preferences in the user's Application Support directory.

## Local work conversations

First-run setup checks the default local work-data folder read-only to determine whether its thread index is supported and how many local conversations are available. It uses the configured folder, `CODEX_HOME`, or `~/.codex`; it does not search unrelated folders. This discovery does not connect the panel, read event-log tails, or install a skill. You explicitly choose **Start tracking real work** before connection; a visible roadmap option controls skill installation.

When you choose to connect ChatGPT Desktop's local work records, the app opens the local thread index read-only and reads bounded event-log tails for activity and structured plans. Chat titles, project labels and task evidence are displayed on your Mac. It does not log in to your account, read auth-token files, or fetch cloud conversations.

Optional manual-unread setup observes a read-to-unread change you make in the desktop app. It uses that verified local identity/host scope; it does not combine accounts or change source read state. Re-run enrollment after changing desktop identities. The state file used for this feature may contain other desktop settings; only scoped unread metadata is retained.

## Roadmap storage

Roadmaps, settings and connection metadata live under `~/Library/Application Support/RoadmapDashboardPreview/`, or a directory you explicitly select. Choosing an existing ledger shares that file rather than copying it. Revision checks prevent a stale view from silently overwriting newer changes. Disconnecting retains records; uninstalling preserves data.

The optional synchronization skill is installed only when selected. Its client follows the active roadmap connection and refuses writes when disconnected. Existing skills, global agent rules and lifecycle hooks are not replaced.

## Local quick search

Roadmap search matches existing task names and project labels already loaded into the panel. Search queries stay in memory, are not saved in preferences or the ledger, and are not sent to a service or model. It does not scan files or conversation content. Text size is an ordinary local view preference.

## Network and model use

Core monitoring, file synchronization and demo mode make no network or background model calls. In prebuilt apps with Sparkle, manual update checks and explicitly enabled background update checks access this project's public GitHub feed and release archives over HTTPS. Background checking is off until chosen and normally runs daily. Optional automatic downloading also allows installation on quit; it does not force a restart. No account or model API is used. Sparkle system profiling is disabled; normal network-request metadata is visible to the download hosts. Update choices are stored in macOS application preferences, and shortcut preferences remain in local shortcut.json. Opening a real conversation explicitly uses its supported desktop link. Agent-side planning can use the model already serving that conversation; that work is subject to the model account's normal usage limits.

## Source archives

The export tool includes only its declared source and sample files. Keep user data outside the source checkout. Inspect the resulting manifest and archive before distributing a build. Local preferences, connection metadata and compiled caches are not needed to build from source.
