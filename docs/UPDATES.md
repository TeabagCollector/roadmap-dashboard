# Updates / 自动更新

Prebuilt releases starting with **0.5.0-preview.6** include [Sparkle 2.10.1](https://github.com/sparkle-project/Sparkle/releases/tag/2.10.1), under its MIT license. Older downloads need one manual replacement first.

## User controls

- First launch asks whether to check for updates. **Not Now** disables background checks and is remembered.
- **Check for Updates…** in the menu bar checks inside the app. **Update Settings…** lets you change your choices.
- Automatic checking uses the public GitHub appcast, normally once a day. It does not call a model or sign in to an account.
- **Download and install on quit** is a separate option, off by default. This is Sparkle's automatic-download behavior: the prepared update can install when you quit Dashboard. It does not force a restart. When ready, Dashboard offers **Install and Reopen** or **On Next Quit**.
- Manual checking remains available with automatic checks disabled. Downloads are verified against the bundled public key before extraction. Invalid signatures or failed downloads leave the current application installed.
- A per-profile single-instance lock prevents duplicate panels and activates the existing one on reopening.
- Local roadmap records, connection configuration and view preferences stay outside the application bundle. Quit any duplicate copy before updating. Updates do not replace your installed roadmap skill or global hooks.

The updater is included in the prebuilt application. A plain `build.sh` source preview without Sparkle keeps a manual releases-page fallback. It does not gain background updates by opening the browser preview.

## Maintainer build and release

1. Run `python3 scripts/fetch_sparkle.py`. It downloads an official archive pinned by version and SHA256 into `artifacts/sparkle/`; it does not install a system-wide dependency. Keep the official license.
2. Generate an independent Sparkle key with the official `generate_keys --account YOUR_KEY_ACCOUNT` tool. Retain the private key in your macOS Keychain and back it up using your own secure process. Store only its public key in `updates/public-key.txt`. Fork maintainers must use their own key, repository/feed URLs and bundle identifier.
3. Build with `scripts/package_macos.py --runtime-archive ... --runtime-notices ... --sparkle-directory artifacts/sparkle/2.10.1 --output ...`. The CPython runtime remains pinned separately. The package embeds Sparkle and its helpers; it retains upstream licenses and ad-hoc signs the preview.
4. Make the application ZIP using `ditto -c -k --sequesterRsrc --keepParent`, preserving framework symlinks. Increase `CFBundleVersion` on every release. Keep bundle identity and application name consistent with the installed build.
5. Run `scripts/make_appcast.py --archive RELEASE.zip --download-url https://.../RELEASE.zip --output updates/appcast.xml --sparkle-directory artifacts/sparkle/2.10.1 --key-account YOUR_KEY_ACCOUNT`. This invokes Sparkle's Keychain signer, verifies the archive signature and emits the public feed. Never export the private key into this repository or an application.
6. Upload and verify the archive before publishing the new appcast. The shipping feed is `https://raw.githubusercontent.com/TeabagCollector/roadmap-dashboard/main/updates/appcast.xml`; payloads are hosted on GitHub Releases. Retain old update archives for installations that have already downloaded an older feed.

The application is currently ad-hoc signed and not notarized. For first-launch macOS security prompts, see the installation guide.

## Verification scope

The isolated harnesses under `tests/updater/` exercise Sparkle's native user settings and the installer using test bundles and a local HTTP fixture server. Local HTTP allowances are limited to those test bundles; the production feed and downloads use HTTPS.

Check both opt-in and opt-out across restarts, both languages, correctly signed archives, corrupted archives, download failure, on-disk replacement and relaunch receipts. Assert that records stored outside the target bundle retain their hashes. An exit-zero result or a changed version label alone is insufficient.

## 中文

从 **0.5.0-preview.6** 起，预编译应用内置 Sparkle；更早版本需要手动覆盖升级一次。

首次询问是否允许检查更新，选择「暂不开启」会记住；顶部菜单的「检查更新…」可在应用内检查，「更新设置…」可修改选择。自动检查默认频率为每天一次，访问公开 GitHub 更新清单，不登录账号、不调用模型。

「自动下载，并在退出时安装」是另一个选项，默认关闭。开启后，新版准备好时可选「安装并重新打开」或「下次退出时安装」，不会强制中断工作。更新包在解压前验证签名；签名不符或下载失败会保留旧程序。清单、主题、语言和连接保存在应用外，不因替换应用丢失；独立安装的 skill 和全局 hook 不会被更新器覆盖。

普通源码预览未链接 Sparkle 时仍使用手动下载入口。首次打开遇到 macOS 安全提示时，请参阅安装说明。
