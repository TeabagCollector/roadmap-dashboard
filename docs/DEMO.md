# Walkthrough / 演示说明

The animated walkthrough uses the public browser preview and fictional data from `src/demo-data.js`, rendered in WebKit. Window framing and captions are presentation styling; the panel content is the public interface.

Five scenes, 2.8 seconds each:

1. Work across projects, with the Notes roadmap collapsed.
2. A simulated Notes reply arrives and becomes unread.
3. The actual task toggle expands its roadmap.
4. A simulated agent report marks keyboard navigation as delivered, pending review. The checkbox stays empty.
5. The actual preview checkbox marks that step complete, representing a user who has checked the result.

The scenes demonstrate separate conversation and task state. A reply arriving does not complete a step. The walkthrough does not show a real model run, live account connection, automatic verification, installation, or a measured synchronization delay. In normal use, the agent and optional roadmap skill write plan and delivery updates to the local ledger. Browser preview changes stay in browser storage; the native app uses its configured ledger.

The English and Chinese walkthroughs show the same actions. Their background is opaque for consistent GIF playback; static screenshots retain transparency and a soft window shadow. No private record is used.

---

中英短演示均使用公开浏览器预览与虚构样例，在 WebKit 中渲染。窗口外框和字幕为展示样式，面板内容来自公开界面。

共五幕，每幕 2.8 秒：跨项目查看工作 → 模拟回复返回并标为未读 → 用真实控件展开路线 → 模拟 agent 上报完成但保留待核验 → 用真实勾选控件代表用户检查后确认完成。

回复返回不代表步骤完成。演示没有运行真实模型，没有接入真实账号，也不表示自动验收或实际同步延迟。正常使用时，由当前 agent 配合可选 skill 维护本机路线清单。所有内容均为虚构，未使用私人记录。
