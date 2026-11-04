# Roadmap Dashboard

A compact macOS companion for **ChatGPT Desktop**, bringing local work conversations and expandable roadmaps into one panel.

[简体中文](README.zh-CN.md) · [Setup guide](docs/CONNECT.md) · [Data handling](docs/PRIVACY.md)

![Roadmap Dashboard in English](docs/preview-en.png)

## What it does

- See working conversations and unread replies without switching between projects.
- Expand each task into a roadmap with checkboxes, progress and acceptance evidence.
- Keep conversation order stable while responses stream.
- Resize the conversation and roadmap sections; scroll them independently.
- Switch between English and Simplified Chinese and choose one of five themes.
- Keep agent-reported delivery separate from verified completion. Manual checks and reopened steps remain under your control.

## Supported conversations

Built and tested with **local Codex-backed work/coding conversations in ChatGPT Desktop on macOS**. It reads the desktop's local work records; it does not connect to your ChatGPT account or retrieve general cloud chat history. Real conversation and task text stays in its original language.

This is an independent companion app. Compatibility with other desktop clients, remote hosts and additional agent runtimes has not been verified. Upstream local record formats may change; unrecognized activity is shown as unknown.

## Try it

For an interactive demo with sample data, open `src/index.html` in a browser. Use **EN / 中** to change language.

For the native app, use macOS 15+, Swift 6 command-line tools and Python 3.9+:

```sh
bash build.sh
"build/Roadmap Dashboard Preview.app/Contents/MacOS/roadmap-dashboard" --language en
```

Or run `python3 scripts/install.py --dry-run` to check installation, then `Install.command` to install in your user Applications folder. Open the gear button to connect local work conversations and choose a roadmap. See the [setup guide](docs/CONNECT.md) for shared roadmaps, optional agent skill setup and removal.

The current release is a source preview, tested on one Apple silicon Mac. The app is ad-hoc signed, not notarized; Intel and second-machine installation remain unverified. Core monitoring and checklist synchronization run locally without background model calls. Agent planning uses the model already handling your conversation.

## Development

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/conversations.test.cjs
```

The optional source export helper is `scripts/export_source.py`. See [data handling](docs/PRIVACY.md) for local storage and permissions, and [related tools](docs/LANDSCAPE.md) for similar projects.

## License

[MIT](LICENSE) · Copyright © 2026 TeabagCollector.
