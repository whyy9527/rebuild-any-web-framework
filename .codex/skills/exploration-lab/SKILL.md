---
name: exploration-lab
description: Use the optional exploration-lab MCP for bounded manual verification with measured feedback, persistent progress and explicit pause.
---

# Exploration Lab

Use only when an explicitly requested task needs the optional manual MCP verifier. Native Goal is the app rebuild continuation owner. Read [the workflow](../../../workflows/harness/WORKFLOW.md) for the manual protocol. The legacy Stop, SessionStart and UserPromptSubmit adapters have been removed; never install or request trust for them. Codex performs reasoning and edits; tools measure frozen checks within a finite budget. Respond to user pauses explicitly through the tools. Do not resume another session's task without explicit paused-task adoption, change acceptance to make checks pass, or start a separate paid model to demonstrate the tool.

Fast same-size Python edits can read stale timestamp bytecode. Harness.verify uses a fresh PYTHONPYCACHEPREFIX per evaluation and disables writes; -B alone does not prevent cache reads.

Native codex mcp add was observed rewriting unrelated server settings. Use the project installer, which owns only its table and Hook entries, backs up files and checks existing settings. Do not restore backups over later user changes indiscriminately.

For a mechanism ablation, commit and push first, freeze the checks, remove one mechanism at a time in isolated copies and report the fixed-check score. Keep model effectiveness claims separate.

## Native CLI appears stalled before verification

Use this recovery only for a CLI/PTY owned by the current task. If tool output stops, inspect its actual Harness state first: a reserved attempt with verification_in_flight unset is different from a running verifier. Silence alone does not establish a crashed host or failed business case.

In native CLI0.162.0-alpha.17.2, an 80×24 PTY stopped painting while awaiting MCP verifier permission. Empty polls, Ctrl-L and WINCH alone did not reveal it; resizing the same owned PTY to100×40 and sending WINCH exposed the pending permission screen. The original session-scoped approval then continued the original attempt successfully. This is a verified UI recovery, not a proven internal cause or universal size requirement.

Resolve the already-known CLI PID's terminal with ps -p <owned-cli-pid> -o tty=. On macOS, after confirming that terminal belongs to this worker, use stty -f /dev/<owned-tty> cols 100 rows 40 and kill -WINCH <owned-cli-pid>, then read the newly rendered screen. Act on the visible permission request under existing authorization; do not send blind Enter, trust unrelated Hooks, permanently allow tools or remove sandboxing.

Preserve task/session IDs, deadline, attempts and actual failures. Do not restart a model/verifier merely to fix painting, patch a live rollout, or count this as automatic model repair. In experiments, record the UI diagnostic intervention and include its wait in wall time; a recovered host does not justify attributing the delay to the ablated mechanism.
