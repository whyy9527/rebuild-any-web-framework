# 架构

本仓库运行在当前 Codex 中。原生 Goal 管理目标和持续执行，Codex 依据 workflow 决策与编辑，RSI 利用历史和反例改进探索，E2E 模具比较原版与候选。

## 当前所有者

| 所有者 | 输入与职责 | 输出 |
| --- | --- | --- |
| 原生 Goal | 用户目标、完成条件、停止／恢复 | 持续执行及最终完成判定 |
| `workflows/rebuild/WORKFLOW.md` | 选择探索或修复、消费反馈、验收与交付的方法 | 当前 Codex 的行动流程 |
| 案例 `rebuild.json` | 案例目标、原版／平台、现有输入路径和命令 argv | 项目入口；不记录运行生命周期 |
| `workflows/rebuild/project.py` | 读取显式项目，使用 `GOAL.template.md` | `create_goal` 参数、只读方法检查、证据索引、现有命令调用；不安装 Hook 或启动模型 |
| `capabilities/rebuild/discovery.py` | 实际状态／动作／输入方式／结果历史 | 已记录的待探索动作；策略选择仍由 Codex 完成 |
| `capabilities/exploration/dream.py` | 多层历史树、可见前缀、可执行策略 | 同一在线／离线决策接口、论文式 (1) 评分、全池策略选择 |
| `runtime/dream.py` | 独立父节点快照、固定命令和协议输入 | 实际发现与评价、不可覆写的树／池、策略进程与胜出文件部署 |
| `workflows/rebuild/dream.py` | 显式案例配置及新输出目录 | collect/replay/cycle/dream/inspect 工作调用，不创建任务生命周期 |
| `capabilities/rebuild/contracts.py` | 共同夹具、场景、断言、两端适配器 | 参考确认、冻结批次、行为比较和覆盖 |
| `frontend.py` / `images.py` / `coverage.py` | 前端契约、实际观测、实测截图与动作库存 | 文字／几何／图像差异和未建模动作 |
| `runtime/browser.py` | 显式浏览器目标、场景动作与就绪条件 | 逐步真实 artifact、实际状态与清理回执；不判产品通过 |
| `capabilities/rebuild/browser.py` | 原版／候选步骤证据与 requirement | 文件摘要、采集稳定性和准备条件门禁，接入 frontend 原断言 |
| `workflows/rebuild/browser.py` | 显式 workspace、scenario 与新输出目录 | 可选 Playwright 的采集 CLI；由项目现有命令或 RSI agent 调用 |
| 案例观察器与驱动 | 真实浏览器或候选 UI 操作 | 状态、资源、截图、音频和动作回执 |
| `runtime/runner.py` | 显式命令与输入 | 命令输出、超时与进程组清理 |

项目清单是新增的连接点，引用已有能力而不复制断言。主文档不维护案例当前版本；由清单指向契约、夹具、历史与命令。运行结果继续落各次独立 artifacts／证据路径，`status` 只读汇总，历史结果明确标为历史，不据此完成 Goal。

`project preflight` 从现有配置与不可变 RSI 产物检查 collect、完整池策略比较、选中策略再部署和共同 E2E 接线；缺失时报告行动，Goal 模板包含创建时的缺口并要求每轮重查。它不运行探针、不保存任务阶段，不根据方法连接齐全判断产品完成；实际执行仍由当前 Codex 按 workflow 消费反馈。

## 原生 Goal 路径

用户选择原版、目标平台和要求 → Codex 读取 workflow 与项目配置 → `project goal` 生成原生 `create_goal` 参数 → 当前 Codex 在授权后调用原生工具。

每轮读取目标、真实历史与实际差异，选择一个能推动用户体验收敛的工作：补原版观察、修观察器、扩充模具或修候选。取得证据后再次比较并选择下一步。RSI 的消费者是这一决策过程及后续实际探针，不要求先证明额外收益。探索时按 [RSI 接口](../workflows/rebuild/RSI.md)从保存的父快照执行、将树加入池、回放策略修订并重新部署。默认策略开发者是当前 Codex；可选 developer 命令只服务本次策略改写，不接管原生 Goal。

树／池是观察证据及选中策略的索引，没有 active、blocked 或 complete 任务状态。回放不能调用真实发现／评价命令，不能提前向决策策略透露未揭露节点。程序接口按可信策略设计，不提供恶意代码 OS 隔离。旧 `projects/exploration-ablation` 的一层回放是历史案例，不是新引擎的默认入口。

新发现进入共同场景和前端契约，两端实际操作后统一判定。业务、视觉、交互、动效和声音同时参与每轮验收；已有测试通过之后仍可回到探索。默认 workflow 不以固定阶段次数、六类检查或至少一个新增行为作为充分性判定。

`project run` 只按 argv 调用清单中的现有命令，使用显式 workspace，拒绝覆盖指定输出；不经 shell，不吞掉验收失败退出码。Duolingo 的 replay 命令连接既有先构建后驱动脚本，compare 连接原严格比较器。它们是封存课程的复跑入口，不是新的原版观察或整站验收。

## E2E 模具边界

业务层由 `contracts.py` 拥有共同动作与 expect，适配器只收到动作和前置状态，返回实际观察。参考确认后冻结，候选使用同批次；新增需求保留父版本。前端层由 `frontend.py` 独立读取状态事实，`images.py` 从实际 PNG 和窗口采样元数据计算比较。平台驱动不能自报通过。

语义、几何、像素和实际音频分别是不同测量；最终以共同用户需求组织交付。当前通用比较器已支持文字、角色、布尔值、矩形、采样颜色和严格整图；动画与声音还依赖案例工具，需求级汇总尚待实现。浏览器 requirement 可引用实际步骤证据，由共同门禁验证就绪、必需文件、采集状态及两端准备后再比较；缺失和不兼容返回 unavailable。采集器保留动效与失败事实，不生成新的验收状态机。详细协议见 [BEHAVIOR-CONTRACT](BEHAVIOR-CONTRACT.md)和[浏览器采集](BROWSER-CAPTURE.md)。

## 兼容运行链

`capabilities/exploration/harness.py` 与 MCP 仅管理手动触发的有界验证尝试／暂停／预算；旧 Hook 适配及自动续跑状态已删除。旧 `capabilities/rebuild/pipeline.py` 管理固定业务批次的阶段与回执。它们保留已有测试和历史宿主证据，供明确需要该模式的环境使用。

原生 Goal 模式不调用安装器或 `exploration_start`。安装器只注册 MCP，并清理显式目标项目中旧安装器拥有的 Hook；不启用 Hook 功能。历史宿主与消融证据保留，复跑需使用记录版本。旧 Pipeline 的 complete 仅表示有界业务批次完成，不能作为完整复刻 Goal 的 verifier；手动用法见 [MCP 验证工具](../workflows/harness/WORKFLOW.md)。

## 案例实现

Duolingo 观察器／契约在 `projects/duolingo-web`；Swift 的 `LearningCore` 拥有学习状态与持久化，`LearningModel` 连接操作和音频，SwiftUI 与原版 Rive／Lottie 资源负责呈现，原生 AX 驱动采集实际自有应用。

线上原版不能完全注入共同夹具或重置服务端，需保留实例、准备路径及限制。API 提供内容不等于 UI 开放对应操作；资源存在不等于已被产品消费。实例数据、平台映射与独立验证事实应保持来源可追溯。

案例尚未 1:1，试验已结束。源码中既有未验证交互修改不属于本次仓库整理的交付；边界见 [案例状态](../projects/duolingo-web/STATUS.md)。批次技术细节与旧文档见 [历史索引](history/README.md)，经验见 [复盘](DUOLINGO-LESSONS.md)。
