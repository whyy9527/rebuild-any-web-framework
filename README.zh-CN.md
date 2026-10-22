# Rebuild Any Web

[English](README.md) | 简体中文

运行在 Codex 中的 App 复刻工作流：**用 RSI 探索原版，用 E2E 构建复刻模具，用原生 Goal 推动 Codex 持续执行。**

RSI 将实际探索保存成历史树，在回放中比较并修订可执行策略，再部署胜出策略回到原版探索；E2E 保存业务与前端要求，验证另一种语言的实现；Goal 保存目标和完成条件。Codex 负责选择行动、操作原版、写代码和读取反馈。


本公开快照包含框架与一个 Duolingo → Swift 案例（含 Swift 客户端）；合成 Dream-RSI 夹具用于验证协议。其他 App 和完整探索档案不在发行范围内。

## 开始使用

让 Codex 读取 [重建工作流](workflows/rebuild/WORKFLOW.md)，提供原版入口、目标平台和完成要求。已有项目使用一份 `rebuild.json` 连接目标、模具与命令。Python 3.11+ 从本仓库根运行：

```sh
python3 -m workflows.rebuild.project goal --workspace . --project projects/duolingo-web/rebuild.json
python3 -m workflows.rebuild.project status --workspace . --project projects/duolingo-web/rebuild.json
```

`goal` 输出可直接传给原生 `create_goal` 的 JSON；由当前 Codex 在用户要求启动时调用工具。命令本身只准备参数，不创建任务、不写 GOAL 文件、不安装 Hook。`status` 展示模具和已保存证据，不把历史通过算成当前产品完成。新项目配置格式与运行方式见 [项目入口](workflows/rebuild/PROJECT.md)。

每轮由目标缺口决定先探索还是先实现：原版观察 → 共同业务／前端模具 → 跨语言实现 → 实际比较 → 根据遗漏与差异改变下一步。主页、内容、布局、字体、图形、交互、动效、声音与持久化从第一轮共同验收；重复跑已有测试无法发现全部遗漏。

## 浏览器采集

按需安装 `python3 -m pip install '.[browser,images]'`，使用调用者已安装的 Chromium 系浏览器：

```sh
python3 -m workflows.rebuild.browser --workspace . --scenario browser.json --out artifacts/browser-new
```

[采集指南](docs/BROWSER-CAPTURE.md)说明显式就绪、逐步证据、launch/connect 资源归属和前端模具接线。截图保留动画和光标；requirement 声明 `browser_capture` 后，共同断言前先核验就绪、文件摘要、采样稳定性及准备条件。采样稳定不代表原子媒体采集或整站完成。

## Duolingo 实践

[Duolingo 网页 → Swift](projects/duolingo-web/README.md)是形成这套方法的实际案例，中文母语学习英语。试验已结束，尚未达到 1:1；已验证能力与缺口见 [案例状态](projects/duolingo-web/STATUS.md)，经验见 [实践复盘](docs/DUOLINGO-LESSONS.md)。查看案例不会自动恢复复刻任务。

Swift 案例需要 macOS、Swift 工具链及原生 UI 驱动所需权限；浏览器观察需要网络和 Playwright，图像比较按需使用 Pillow。案例命令通过同一项目入口调用：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command build
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command launch --out artifacts/review-new
```

`--out` 使用尚不存在的路径。原版与候选分别准备状态，线上刷新不等于服务端重置。

## 文档与验证

- [Workflow](workflows/rebuild/WORKFLOW.md)：Codex 的执行方法与 Goal 调用。
- [RSI 接口](workflows/rebuild/RSI.md)：历史树、离策略回放、策略修订及实际部署；[可跑检查](projects/dream-rsi-check/README.md)。
- [哲学](docs/PHILOSOPHY.md)、[架构](docs/ARCHITECTURE.md)、[业务／前端协议](docs/BEHAVIOR-CONTRACT.md)：原则、职责和可执行模具。
- [Roadmap](docs/ROADMAP.md)：仓库下一步成果；[方法来源](docs/RESEARCH.md)：Dream-RSI 的探索思路与 Cordis 的组合设计。
- [历史索引](docs/history/README.md)：批次记录、原始证据和旧文档。README 不记录逐轮进展。
- [验证环境](docs/ENVIRONMENT.md)：依赖声明、锁定安装和无头验证。
- [框架发行与公开快照同步](docs/RELEASING.md)：从已提交源码生成纯框架快照、验证及发布。

```sh
python3 -m unittest discover -v
```

原生 Goal 是持续执行入口。旧 Stop Hook 已删除；手动 MCP 验证工具不负责自动续跑。消融用于完成复刻后的优化，顺序见工作流。

## 版本与许可

版本下载见 [GitHub Releases](https://github.com/whyy9527/rebuild-any-web-framework/releases)，版本变化见 [CHANGELOG](CHANGELOG.md)。原创代码与文档采用 [MIT](LICENSE)；Duolingo 素材、采集内容和依赖的授权边界见 [第三方说明](THIRD_PARTY_NOTICES.md)。本仓库是独立的复刻方法实践，与 Duolingo 或 OpenAI 没有隶属或背书关系。

框架来源和逐文件摘要见 `FRAMEWORK-SOURCE.json`。
