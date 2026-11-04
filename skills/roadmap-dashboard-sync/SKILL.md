---
name: roadmap-dashboard-sync
description: Maintain explicitly authorized substantive work in the local Roadmap Dashboard ledger at plan, delivery, blocker and acceptance checkpoints. Exclude casual discussion and one-turn questions.
---

Use only after the user has chosen to track their work in this app. This skill does not grant publishing, deployment, cross-agent communication or workspace creation authority.

Use the installed local `dashboard_client.py status` command to inspect the current connection and `dashboard_client.py request` to read or mutate its active ledger with JSON on stdin. The setup flow appends the actual local launcher path after installation; this public template contains no developer path. Never invent a data directory, create a second ledger, or operate on the demo ledger. If disconnected, ask the user to connect the app first.

At the beginning of substantive authorized work, read {"op":"get"}, match the goal and reuse an existing task ID. Register a plan with the returned revision and stable step IDs; statuses are pending/in_progress/completed. Update at real plan changes, delivery, blocker changes and verification, not each message. Exclude casual questions, hypothetical discussion and tiny one-turn answers. New tasks need the actual source chat ID and observable completion criteria.

`report` records execution without acceptance. `accept` is for the supervising agent's independently checked evidence; reported delivery and a finished chat are not completion. Preserve manual user decisions. The local client refuses the UI's user-only `check` operation. Re-read the ledger on revision conflict rather than forcing an overwrite.

Only local record maintenance is authorized by this skill. It grants no deployment, publication, cross-agent messaging, new workspaces or recurring model calls. No hook is installed by the setup flow. Other accounts, machines, ordinary ChatGPT chats and independent agent internals are outside the configured live source.


Request forms (JSON on stdin; use the current revision):

- `{"op":"get"}` reads the active ledger.
- `{"op":"plan","revision":N,"id":"stable-goal-id","title":"Goal","project":"Existing project","threadId":"actual-source-chat-uuid","steps":[{"id":"stable-step-id","text":"Concrete action","criterion":"Observable completion condition","status":"pending"}]}` registers or revises an agreed plan.
- `{"op":"report","revision":N,"taskId":"stable-goal-id","stepId":"stable-step-id","status":"in_progress","evidence":"Actual execution result or blocker"}` reports status; completed still needs review.
- `{"op":"accept","revision":N,"taskId":"stable-goal-id","stepId":"stable-step-id","evidence":"Independent verification result"}` records supervisor acceptance.

Do not replace a plan from a truncated chat excerpt, infer completion from title/status, or clear a user's manual choice. Reuse IDs and keep the actual agreed scope.
