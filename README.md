# Rebuild Any Web

English | [简体中文](README.zh-CN.md)

**Rebuild apps in Codex with RSI exploration, shared end-to-end tests, and native Goals.**

Explore an existing app, capture its behavior and frontend requirements in a shared test mold, and implement it on a target platform. Codex chooses actions, operates the reference, writes code, and uses measured differences to guide the next step.

RSI (recursive self-improvement) records exploration as a history tree, compares executable exploration policies through replay, and deploys the selected policy back to the reference app. E2E tests compare reference and candidate behavior and presentation. Native Codex Goals own the objective, continued execution, and completion criteria.


This public snapshot contains the framework and one Duolingo → Swift case, including its Swift client. The synthetic Dream-RSI fixture tests the protocol. Other apps and the full exploration archive are excluded.

## Getting started

Clone this repository and open it in Codex. Ask Codex to read the [rebuild workflow](workflows/rebuild/WORKFLOW.md), then provide the reference app, target platform, and acceptance requirements. Most detailed workflow documents are currently in Chinese.

Each project uses one `rebuild.json` to connect its objective, test molds, evidence, and commands. With Python 3.11+, run from the repository root:

```sh
python3 -m workflows.rebuild.project goal --workspace . --project projects/duolingo-web/rebuild.json
python3 -m workflows.rebuild.project status --workspace . --project projects/duolingo-web/rebuild.json
```

`goal` prints JSON for Codex's native `create_goal` tool. Codex calls that tool when you request a Goal; the command itself only prepares arguments. `status` reads saved evidence and test molds. Historical passes do not establish that the current app is complete. See the [project configuration guide](workflows/rebuild/PROJECT.md) to add your own project.

The working cycle is reference observation → shared behavior/frontend requirements → implementation → actual comparison → the next exploration or repair. Include content, home screens, layout, fonts, assets, interactions, animation, sound, and persistence from the first round. Repeating existing tests alone cannot reveal every missing requirement.

Native Goals provide continued execution. The legacy Stop Hook has been removed; the optional manual MCP verifier does not resume Codex automatically. Mechanism ablations belong **after** reconstruction and full acceptance, as described in the workflow's optimization stage.

## Browser capture

Use the [locked verification environment](docs/ENVIRONMENT.md) for development and release checks. For an optional application install, use `python3 -m pip install '.[browser,images]'`, then use an already-installed Chromium-family browser:

```sh
python3 -m workflows.rebuild.browser --workspace . --scenario browser.json --out artifacts/browser-new
```

The [browser capture guide](docs/BROWSER-CAPTURE.md) describes explicit readiness, per-step evidence, launch/connect ownership, and integration with existing frontend tests. Capture keeps animation and caret behavior. A declared `browser_capture` reference makes readiness, artifact integrity, sampled state stability, and preparation checks mandatory before the shared assertion runs. This does not establish atomic media capture or whole-app completeness.

## Case studies

[Duolingo web → Swift](projects/duolingo-web/README.md) informed this workflow through a real reconstruction for Chinese speakers learning English. The experiment has ended and did not reach 1:1 parity. Read the [case status](projects/duolingo-web/STATUS.md) and [lessons learned](docs/DUOLINGO-LESSONS.md) for verified capabilities and remaining gaps.

The Swift case requires macOS, a Swift toolchain, and permissions for native UI automation. Browser observation requires network access and Playwright; image comparison uses Pillow when needed. Run case commands through the same project entry point:

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command build
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command launch --out artifacts/review-new
```

Use a new path for `--out`. Prepare reference and candidate state separately; refreshing an online app does not reset server state.

## Documentation and verification

- [Workflow](workflows/rebuild/WORKFLOW.md): execution method and native Goal setup.
- [RSI protocol](workflows/rebuild/RSI.md): history trees, policy replay, revision, and deployment; [runnable protocol checks](projects/dream-rsi-check/README.md).
- [Philosophy](docs/PHILOSOPHY.md), [architecture](docs/ARCHITECTURE.md), and [behavior/frontend contract](docs/BEHAVIOR-CONTRACT.md): principles, ownership, and shared tests.
- [Roadmap](docs/ROADMAP.md) and [research](docs/RESEARCH.md): unfinished outcomes and the Dream-RSI/Cordis sources.
- [History](docs/history/README.md): experiment records and original evidence.
- [Environment](docs/ENVIRONMENT.md): declared dependencies, locked installation, and headless verification.
- [Framework releases](docs/RELEASING.md): packaging, verification, and public snapshot sync.
- [Browser capture](docs/BROWSER-CAPTURE.md): CLI observations and frontend evidence checks.

```sh
python3 -m unittest discover -v
```

## Releases and license

See [GitHub Releases](https://github.com/whyy9527/rebuild-any-web-framework/releases) for downloads and the [changelog](CHANGELOG.md) for changes. Original code and documentation are [MIT licensed](LICENSE). Captured content, Duolingo assets, and dependencies have separate boundaries in [third-party notices](THIRD_PARTY_NOTICES.md).

This is an independent app reconstruction project, with no affiliation with or endorsement by Duolingo or OpenAI.

Framework provenance and file digests: `FRAMEWORK-SOURCE.json`.
