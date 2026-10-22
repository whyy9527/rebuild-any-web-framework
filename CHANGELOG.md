# Changelog

## 0.5.0 — 2026-10-22

- Extract Block Killer into an independent private repository under `xinxiayiyan`; preserve its existing production URL.
- Remove the ended Duolingo/Swift implementation, assets and case-only tests from the current tree and retire the sample export mode. Framework distributions now contain only framework code, methods, tests and the synthetic Dream-RSI fixture.
- Retire six historical experiment trees. Preserve their findings, limitations and exact recovery commit through one history index; current tests and packaging no longer read those archives.
- Update entrypoints, skills and license notices to the surviving owners. Historical releases remain historical and are not rewritten.

## 0.4.0 — 2026-10-22

- Move the VALORANT predictor and S16 website into independent private repositories under `xinxiayiyan`; their code, tests and deployment maintenance belong to those repositories. Existing deployed services remain in place.
- Remove the Block Killer publisher's runtime import of the migrated VALORANT project; keep only its required transport in the case. No production rollout is part of this change.
- Replace the browser fixture's platform-dependent End key with caret navigation; preserve strict capture stability and pixel assertions.
- Declare Pillow as the optional `images` dependency and ship a hash-locked browser/image verification environment with the framework.
- Carry the headless-only browser verification policy into exported snapshots and remove references to excluded cases from public agent instructions.
- Refresh the public framework and Duolingo Swift sample from one committed source snapshot, with file digests and independently verified release archives.

The Duolingo and Block Killer experiments remain ended. This maintenance release does not establish complete App parity or complete the open framework roadmap.

## 0.3.0 — 2026-10-15

- Rename the project and source repository to Rebuild Any Web / `rebuild-any-web`.
- Add an optional Playwright browser capture CLI with explicit launch/connect targets, per-step readiness, original animation/caret behavior, measured preparation, artifact digests, and partial failure receipts.
- Connect browser evidence to the existing frontend mold: verify reference/candidate identity, readiness, artifact integrity, sampled stability, and preparation before comparing actual text, elements, or pixels.
- Verify delayed and wrong results, screenshot/font failure, DOM drift, input modes, motion preservation, Service Workers, and external-browser cleanup through a real browser and public CLI against a source-owned fixture.
- Publish the same framework-only snapshot and release assets to the personal and organization repositories. Real App cases and private inputs remain outside the framework package.

Sampled stability does not establish atomic capture or full animation/audio parity. Browser relative-geometry origins and native/media preparation remain unfinished; this release does not claim complete autonomous reconstruction of an arbitrary site.

- Remove the legacy Stop Hook and lifecycle adapter; native Goals own continuation. Keep optional manual MCP verification and migrate owned project Hook registrations without changing other configuration.
- Make the main README English, add `README.zh-CN.md`, and update GitHub discovery metadata.

## 0.2.0 — 2026-10-13

- 新增项目入口 `preflight`，校验真实RSI池、同池策略比较、选中策略及实际再次部署；将缺口接入原生Goal参数。
- 通用前端比较器新增 `element_value`，比较实际字符串输入值，缺失或错误类型保留为不可用。
- 将真实反例落实到rebuild方法，区分已修订规则与尚未实现能力；核对组织纯框架快照的同步范围。
- 实现 Dream-RSI 第 3 节的多层历史树、可见前缀回放、rho 扫描评分、全历史池策略改进与实际再次部署。
- 在 rebuild workflow 接入 collect/replay/cycle；当前 Codex 可直接消费反馈并修订可执行策略，原生 Goal 仍拥有持续运行。
- 保存可复跑协议夹具及当前会话真实修订记录，保留失败策略；更新方法、职责与研究实现对应。

框架专用发行包仅包含原创框架、方法文档、测试与合成协议夹具；不包含App实现、原版素材、私有账号或历史快照。组织仓库同步同一份框架快照与发行包，来源及文件摘要由包内 `FRAMEWORK-SOURCE.json` 记录。

完整App仍未达到1:1。共用原生采集器、比较前置条件判定、需求级汇总和真实分支策略效果验证仍在Roadmap；本版本不声明完成这些能力。

## 0.1.0 — 2026-10-12

首次公开的源码版本，将 Duolingo 网页到 Swift 实践形成的方法整理为可在 Codex 中使用的 rebuild 工作流。

- 用 RSI 的历史反馈改进探索，用共同业务与前端 E2E 保存复刻要求，用原生 Goal 管理目标及持续执行。
- 提供项目配置、薄 Goal 模板，以及 `goal`、`status`、`run` 统一入口；保留真实失败退出码及证据。
- 从第一轮覆盖主页、内容、交互、布局、动效、声音和持久化；发现遗漏后修订模具，再验证实现。
- 收敛 README、AGENTS、哲学、架构及 Roadmap；案例历史与研究记录独立保存，原论文和负面实验结果保留。
- 将消融置于完整复刻、验收和可运行基线交付之后的优化阶段。
- 修复新会话测试发现的 `.cjs` 源码摘要遗漏；评估期间修改 CommonJS 源码会使成功回执失效。
- 为原创代码与文档加入 MIT 许可，并单独说明第三方内容的授权范围。

验证：`python3 -m unittest discover -v` 的 74 项测试通过。独立新 Codex 会话以小型 Python／JavaScript 夹具走通真实探索、模具修订、修复和干净副本复跑，6 条业务场景、10 项前端要求通过，实际触发音频 PCM 相同，并观察到一次原生 Goal 自动接续。长期无人运行及重启恢复仍未验证。

版本不附带已完成 Duolingo 复刻或整站 1:1 的声明；该案例已结束且仍有差异。旧 Harness/Pipeline 为显式选择的兼容入口，不能与原生 Goal 同时续跑同一任务。源码包含较大的历史证据，尚未验证的本地 Swift 修改不在本版本中。
