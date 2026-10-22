# Rebuild Any Web

[English](README.md) | 简体中文

运行在 Codex 中的 App 复刻框架：**用 RSI 探索原版，用共同 E2E 保存要求，用原生 Goal 推动持续执行。**

Codex 负责观察、编写实现和读取差异。RSI 通过历史回放比较可执行策略，再将选中策略部署到真实探索；业务和前端模具共用两端要求，原生 Goal 拥有持续执行和完成判定。

本仓库维护框架、工作流、测试和研究经验，业务 App 在独立消费仓库实施。`projects/` 当前只保留合成 Dream-RSI 协议夹具。公开发行位于 [rebuild-any-web-framework](https://github.com/whyy9527/rebuild-any-web-framework)。

## 开始使用

让 Codex 读取[重建工作流](workflows/rebuild/WORKFLOW.md)，提供原版、目标平台与验收要求。在独立 App 工作区按[项目入口](workflows/rebuild/PROJECT.md)建立一份 `rebuild.json`，连接目标、模具、证据和命令。

需要 Python 3.11+，维护复验使用[锁定环境](docs/ENVIRONMENT.md)。将框架安装到消费项目的环境并准备好配置后，从该项目根运行：

```sh
python3 -m workflows.rebuild.project goal --workspace . --project rebuild.json
python3 -m workflows.rebuild.project status --workspace . --project rebuild.json
```

`goal` 只准备原生 `create_goal` 参数；只有用户要求启动时才创建 Goal。`status` 读取证据与方法接线，不将历史通过算作当前产品完成。

在框架根可检查附带的合成协议夹具：

```sh
python3 -m workflows.rebuild.project status --workspace . --project projects/dream-rsi-check/rebuild.json
```

每轮按缺口选择观察或实现：原版观察 → 共同业务／前端要求 → 实现 → 实际比较 → 下一次探索或修复。内容、导航、布局、字体、素材、交互、动效、声音和持久化从第一轮一起验收；协议夹具通过不代表 App 完整。已结束案例不自动恢复探索。

## 浏览器采集

可选 CLI 使用显式 Chromium 系可执行文件、逐步就绪条件和实际采集回执：

```sh
python3 -m workflows.rebuild.browser --workspace . --scenario browser.json --out artifacts/browser-new
```

在消费工作区准备场景并使用新输出目录。[采集指南](docs/BROWSER-CAPTURE.md)说明 launch/connect 归属、状态采样、摘要和共同前端断言。采样稳定不代表原子媒体采集或整站 1:1；自动浏览器验证使用无头模式。

## 文档与验证

- [Workflow](workflows/rebuild/WORKFLOW.md)、[项目配置](workflows/rebuild/PROJECT.md)、[RSI 协议](workflows/rebuild/RSI.md)。
- [合成协议夹具](projects/dream-rsi-check/README.md)：算法和运行接线检查。
- [哲学](docs/PHILOSOPHY.md)、[架构](docs/ARCHITECTURE.md)、[业务／前端协议](docs/BEHAVIOR-CONTRACT.md)。
- [验证环境](docs/ENVIRONMENT.md)、[框架发行](docs/RELEASING.md)、[Roadmap](docs/ROADMAP.md)。
- [研究](docs/RESEARCH.md)、[Duolingo 经验](docs/DUOLINGO-LESSONS.md)、[历史退役索引](docs/history/retirement-2026-10-22.md)。

```sh
python3 -m unittest discover -v
```

## 发行与许可

专用框架包见 [GitHub Releases](https://github.com/whyy9527/rebuild-any-web-framework/releases)。变更见 [CHANGELOG](CHANGELOG.md)，原创代码与文档遵循 [MIT](LICENSE)，第三方范围见[许可通知](THIRD_PARTY_NOTICES.md)。

本项目独立于 OpenAI 及历史研究中的各个 App，不表示合作或背书。

框架来源和逐文件摘要见 FRAMEWORK-SOURCE.json。
