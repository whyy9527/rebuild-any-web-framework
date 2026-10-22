# Rebuild Any Web

English | [简体中文](README.zh-CN.md)

**Rebuild apps in Codex with RSI exploration, shared end-to-end tests, and native Goals.**

Codex observes a reference app, records behavior and frontend requirements in a shared test mold, implements a candidate, and uses measured differences to choose the next action. RSI compares executable exploration policies through historical replay and deploys the selected policy back to real exploration. Native Goals own continued execution and completion criteria.

This repository owns the framework, workflows, tests, and research lessons. App implementations live in independent consumer repositories. `projects/` contains only the synthetic Dream-RSI protocol fixture. The public distribution is [rebuild-any-web-framework](https://github.com/whyy9527/rebuild-any-web-framework).

## Getting started

Open the framework in Codex and read the [rebuild workflow](workflows/rebuild/WORKFLOW.md). Provide the reference app, target platform, and acceptance requirements. Create the app in its own workspace and follow the [project configuration guide](workflows/rebuild/PROJECT.md) to connect its objective, test molds, evidence, and commands through one `rebuild.json`.

Use Python 3.11+ and the [locked verification environment](docs/ENVIRONMENT.md). Once the framework is installed in the consumer environment and its project configuration exists, run from that consumer workspace:

```sh
python3 -m workflows.rebuild.project goal --workspace . --project rebuild.json
python3 -m workflows.rebuild.project status --workspace . --project rebuild.json
```

`goal` prepares arguments for Codex's native `create_goal` tool; it does not create a Goal. `status` reads recorded evidence and method wiring. Neither historical passes nor a complete protocol fixture establish App completeness.

To inspect the bundled synthetic fixture from this repository root:

```sh
python3 -m workflows.rebuild.project status --workspace . --project projects/dream-rsi-check/rebuild.json
```

The working cycle is reference observation → shared behavior/frontend requirements → implementation → actual comparison → the next exploration or repair. Include content, navigation, layout, fonts, assets, interaction, animation, sound, and persistence from the first round. Ended cases stay ended unless the user requests new work.

## Browser capture

The optional browser CLI uses an explicit installed Chromium-family executable, per-step readiness, and actual capture receipts:

```sh
python3 -m workflows.rebuild.browser --workspace . --scenario browser.json --out artifacts/browser-new
```

Prepare the scenario in the consumer workspace and use a new output path. The [capture guide](docs/BROWSER-CAPTURE.md) explains launch/connect ownership, sampled state stability, artifact digests, and frontend assertion integration. Sampling does not establish atomic media capture or whole-App parity. Automated browser verification runs headlessly.

## Documentation and verification

- [Workflow](workflows/rebuild/WORKFLOW.md), [project configuration](workflows/rebuild/PROJECT.md), and [RSI protocol](workflows/rebuild/RSI.md).
- [Protocol fixture](projects/dream-rsi-check/README.md): executable algorithm checks.
- [Philosophy](docs/PHILOSOPHY.md), [architecture](docs/ARCHITECTURE.md), and [behavior/frontend contract](docs/BEHAVIOR-CONTRACT.md).
- [Environment](docs/ENVIRONMENT.md), [framework releases](docs/RELEASING.md), and [roadmap](docs/ROADMAP.md).
- [Research](docs/RESEARCH.md), [Duolingo lessons](docs/DUOLINGO-LESSONS.md), and [historical retirement index](docs/history/retirement-2026-10-22.md).

```sh
python3 -m unittest discover -v
```

## Releases and license

Download dedicated framework archives from [GitHub Releases](https://github.com/whyy9527/rebuild-any-web-framework/releases). See the [changelog](CHANGELOG.md), [MIT license](LICENSE), and [third-party notices](THIRD_PARTY_NOTICES.md).

This is an independent project with no affiliation with or endorsement by OpenAI or the apps studied in its historical cases.

Framework provenance and file digests: FRAMEWORK-SOURCE.json.
