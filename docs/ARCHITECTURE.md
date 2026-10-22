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

业务源码、场景、契约和证据由独立消费项目拥有；本仓库 `projects/` 只保留合成协议夹具。项目清单引用已有能力而不复制断言。主文档不维护案例当前版本；由清单指向契约、夹具、历史与命令。运行结果继续落各次独立 artifacts／证据路径，`status` 只读汇总，历史结果明确标为历史，不据此完成 Goal。

`project preflight` 从现有配置与不可变 RSI 产物检查 collect、完整池策略比较、选中策略再部署和共同 E2E 接线；缺失时报告行动，Goal 模板包含创建时的缺口并要求每轮重查。它不运行探针、不保存任务阶段，不根据方法连接齐全判断产品完成；实际执行仍由当前 Codex 按 workflow 消费反馈。

## 原生 Goal 路径

用户选择原版、目标平台和要求 → Codex 读取 workflow 与项目配置 → `project goal` 生成原生 `create_goal` 参数 → 当前 Codex 在授权后调用原生工具。

每轮读取目标、真实历史与实际差异，选择一个能推动用户体验收敛的工作：补原版观察、修观察器、扩充模具或修候选。取得证据后再次比较并选择下一步。RSI 的消费者是这一决策过程及后续实际探针，不要求先证明额外收益。探索时按 [RSI 接口](../workflows/rebuild/RSI.md)从保存的父快照执行、将树加入池、回放策略修订并重新部署。默认策略开发者是当前 Codex；可选 developer 命令只服务本次策略改写，不接管原生 Goal。

树／池是观察证据及选中策略的索引，没有 active、blocked 或 complete 任务状态。回放不能调用真实发现／评价命令，不能提前向决策策略透露未揭露节点。程序接口按可信策略设计，不提供恶意代码 OS 隔离。早期单层回放已退役，原始实验保存在[历史归档](history/retirement-2026-10-22.md)。

新发现进入共同场景和前端契约，两端实际操作后统一判定。业务、视觉、交互、动效和声音同时参与每轮验收；已有测试通过之后仍可回到探索。默认 workflow 不以固定阶段次数、六类检查或至少一个新增行为作为充分性判定。

`project run` 只按 argv 调用清单中的现有命令，使用显式 workspace，拒绝覆盖指定输出；不经 shell，不吞掉验收失败退出码。消费项目拥有自己的构建、驱动与比较命令；已结束案例的历史命令不再作为框架入口。

## E2E 模具边界

业务层由 `contracts.py` 拥有共同动作与 expect，适配器只收到动作和前置状态，返回实际观察。参考确认后冻结，候选使用同批次；新增需求保留父版本。前端层由 `frontend.py` 独立读取状态事实，`images.py` 从实际 PNG 和窗口采样元数据计算比较。平台驱动不能自报通过。

语义、几何、像素和实际音频分别是不同测量；最终以共同用户需求组织交付。当前通用比较器已支持文字、角色、布尔值、矩形、采样颜色和严格整图；动画与声音还依赖案例工具，需求级汇总尚待实现。浏览器 requirement 可引用实际步骤证据，由共同门禁验证就绪、必需文件、采集状态及两端准备后再比较；缺失和不兼容返回 unavailable。采集器保留动效与失败事实，不生成新的验收状态机。详细协议见 [BEHAVIOR-CONTRACT](BEHAVIOR-CONTRACT.md)和[浏览器采集](BROWSER-CAPTURE.md)。

## 兼容运行链

`capabilities/exploration/harness.py` 与 MCP 仅管理手动触发的有界验证尝试／暂停／预算；旧 Hook 适配及自动续跑状态已删除。旧 `capabilities/rebuild/pipeline.py` 管理固定业务批次的阶段与回执。它们保留已有测试和历史宿主证据，供明确需要该模式的环境使用。

原生 Goal 模式不调用安装器或 `exploration_start`。安装器只注册 MCP，并清理显式目标项目中旧安装器拥有的 Hook；不启用 Hook 功能。历史宿主与消融证据保留，复跑需使用记录版本。旧 Pipeline 的 complete 仅表示有界业务批次完成，不能作为完整复刻 Goal 的 verifier；手动用法见 [MCP 验证工具](../workflows/harness/WORKFLOW.md)。

## 消费项目与历史

瓦站、S16 和方块杀手分别由以下独立私有仓库维护：

- [xinxiayiyan/valorant-predictor](https://github.com/xinxiayiyan/valorant-predictor)
- [xinxiayiyan/s16](https://github.com/xinxiayiyan/s16)
- [xinxiayiyan/block-killer](https://github.com/xinxiayiyan/block-killer)

业务实现、资源、产品测试、数据与部署入口由各自仓库拥有；框架只提供通用算法和可安装 CLI。
共享云基础设施仍由其既有所有者维护，拆源码不自动变更线上地址、网关或用户存档。

Duolingo／Swift 与六组历史实验已从当前树删除，样例分发模式已退役。
[归档索引](history/retirement-2026-10-22.md)保留冻结提交、原始结论、失败及恢复方式。
框架的当前测试、构建和打包不读取这些归档，不以旧回执证明当前产品完成。
