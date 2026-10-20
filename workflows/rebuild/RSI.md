# Dream-RSI 探索接口

本模块按 [Dream-RSI 第 3 节](https://arxiv.org/html/2609.14858v2)独立实现历史树、回放评分、策略改进和再次部署。策略决定从哪里继续、并行多少请求和何时停止；发现 agent 与评价协议保持固定。回放使用已有结果，不假装探索了尚未记录的世界。

## 在当前 Codex 中使用

默认由当前 Codex 担任策略开发者，原生 Goal 推进工作。准备案例的可恢复状态与固定发现／评价命令后，在 `rebuild.json` 的 `inputs.rsi_config` 指向下面的配置，`commands` 接入 `collect` 和 `replay`。这些是一次工作调用，没有 Goal 状态、Hook 或另一个续跑器。

1. `collect` 用当前策略实际运行探针，保存父子树、独立工作区快照、生成上下文、评价与命令回执。首次从 seed 开始，随后用 `--pool` 读取上次选出的策略和全部历史。
2. `replay` 先评价当前策略。当前 Codex 读取生成的 `evaluation.json` 中各世界、各 rho 的轨迹、分数和失败，修订可执行策略文件。
3. 再次 `replay`，把本次所有修订依次用 `--candidate` 传入；每版都在同一冻结历史池上评价，保留原策略参与选择。继续修订时读取上一版真实反馈，保留已失败版本。
4. 将输出 `pool.json` 传给下一次 `collect`，真正部署胜出的文件。发现的新要求接入 E2E；分数不能代替需求验收。原版证据不足时仍需主动寻找新入口，历史回放本身不会产生未知结果。

```sh
python3 -m workflows.rebuild.dream collect --workspace . --config <rsi.json> --out artifacts/rsi-collect
python3 -m workflows.rebuild.dream replay --workspace . --config <rsi.json> --pool artifacts/rsi-collect/iteration-1/collected-pool.json --out artifacts/rsi-baseline
python3 -m workflows.rebuild.dream replay --workspace . --config <rsi.json> --pool artifacts/rsi-collect/iteration-1/collected-pool.json --candidate <policy-v1.py> --candidate <policy-v2.py> --out artifacts/rsi-revisions
python3 -m workflows.rebuild.dream collect --workspace . --config <rsi.json> --pool artifacts/rsi-revisions/pool.json --out artifacts/rsi-next
```

已配置固定 `reviser` 时也可用 `cycle --iterations N` 完成在线→离线→部署；`dream --pool ...` 仅做离线改进。两者显式调用该命令，不暗中选择模型。`inspect --pool ...` 只读验证历史及策略哈希。`replay` 与 `dream` 不调用发现 agent 或评价器。

## 案例配置与命令协议

完整可跑配置见 [协议夹具](../../projects/dream-rsi-check/dream.json)。所有路径相对显式工作区；命令是 argv，不经过 shell。输出使用新目录，已保存快照及策略不可覆写。

| 字段 | 含义 |
| --- | --- |
| `schema_version: 1` | 当前协议 |
| `seed`、`root_observation` | 独立恢复的初始目录及已确认初始事实 |
| `initial_policy` | 首次策略 Python 文件，定义 `select(view, rho)` |
| `agent`、`evaluator` | 固定发现／独立评价命令 argv |
| `reviser` | 可选固定策略开发命令；当前 Codex 直接修订时省略 |
| `fixed_inputs` | 非空文件／目录列表：提示、观察器、评价器及其依赖等；命令参数中实际存在的脚本也自动校验 |
| `score_semantics` | 固定、越大越好的质量定义；不能用 agent 自报分数或控件数量冒充前端完整性 |
| `workers`、`online_rounds`、`replay_rounds` | 并行上限 W、在线 K1、回放 K2 |
| `versions` | 自动 cycle/dream 的版本数 M，包含原策略；当前 Codex 路径由传入文件数确定 |
| `parallelism_penalty`、`timeout_seconds` | 论文 λ 与单次命令时限 |

每个命令读 stdin JSON，只向 stdout 写一个 JSON；过程日志自行保存在回执目录。调用目录中有 `request.json`，命令退出码、超时、输出与实际结果分别保留。

| 命令 | 接收 | 返回 |
| --- | --- | --- |
| `agent` | `workspace`：已从父节点恢复的独立目录；`parent`、当前可见 `prefix`、分开提供的 `completed_history`、创建序号 `attempt` | `generation`：本次上下文记录；`observation`：实际事实对象。探针／代码／证据写入工作区 |
| `evaluator` | `workspace`，不接收期待通过的答案 | `score`：有限数；`observation`：独立检查及证据。真实 App 须实际操作并采集 UI／音频 |
| `reviser` | `interface`、当前 `policy_code`、所有先前 `feedback`、版本号 | `code`：完整 Python 策略源码 |

固定协议身份覆盖命令、解释器、脚本、显式输入、seed 和评分定义。依赖、模型／提示、观察器或评价语义改变时更新固定输入，使用新池；同一轮比较不能混用。运行快照、候选源码与结果的哈希用于检测历史修改；不是恶意程序的安全证明。

原版 App 的会话／本地状态恢复由案例发现命令完成，记录实际准备路径。仅复制浏览器代码不会恢复远程服务端；尚不能恢复的分支保留限制，不伪称具备任意状态回放。

## 原生 UI 协议准备

原生探针先区分来源、加载就绪与恢复路径：

- 控件在实际弹窗或区域内查找，不能命中背景同名文字。标题出现、两次 captions 相等都不证明数据已加载；等待本动作所需的实际记录／输入／复选框。准备阶段因刷新短暂缺少 HTML 节点时可有界等待正确来源重新出现，其他来源仍拒绝，业务阶段仍要求目标页面。
- 恢复应包含真实中间态，例如刷新后提醒、主页入口加载与返回业务页。只记录实际可验证的本地表单丢弃，不称为远程重置。取得进程终态或确认仍活后再决定接续／新运行；主动终止错误协议时清理其拥有的评价进程，保留部分回执。
- 解析 AX 时限定目标元素，保留 cell Value 与字段显式 Value，不能把邻近链接 Value 当成输入值。实际平台也可能把数字写在字段名称中；仅按已观察原文支持该表示，不能从请求或期望回填缺失值。解析失败后用已保存的真实 AX／截图做离线反例检查，再冻结修订；评价仍需独立实际操作。
- AX 与截图分别采集可能跨越加载变化；核对两者确为同状态。相同视口尺寸不保证相同滚动、焦点或悬停。保存实际不一致，不用局部语义通过替代前端验收。
- 原生调用须在有效工具执行上下文内 await 完成，不能让未完成 Promise 跨工具返回继续操作。长探针拆成显式可检查的调用边界，保持宿主可响应；这不另建 Goal 生命周期。

评分应说明衡量的是重复采集、分支发现还是其他已验证质量。固定两个探针重复成功、停止策略提高回放分数，不证明探索了更广需求或复刻质量提高。已有协议可接续时保留历史；新协议的必要性来自实际恢复／观察／评价变化，不能只为重复获得更高分拆细批次。

展示探索树时，从项目清单读取现有页面历史和当前池，先校验不可变产物，再画实际父子关系。页面状态文件与 RSI 世界各自保留来源，展示分组不伪称环境转移；保留重复分支、不可用操作、未记录结果及未形成新世界的再部署。节点数、分数和空白分支都不转成产品完成率；生成视图只读，不触发新探针或接续 Goal。

## 策略与回放语义

`select(view, rho)` 返回互异节点 ID 列表，最多 W 个，空列表停止。`view.nodes` 只有当前揭露节点的 `id/parent/seq/score/observation/generation_history`；`view.eligible` 是根及可见叶节点，另有 `round` 与 `max_parallelism`。策略从前缀重建自己的判断，不依赖跨调用内存。在线与离线使用同一接口。

每个非根节点保留唯一父节点及继承的生成记录。根可开多个分支；非根被延续后不再是叶，因此只能有一个直接子节点。并行结果按选择顺序提交创建序号，不以执行完成速度改变回放顺序。回放选根时揭露最早创建、尚未揭露的根子节点；选非根时只揭露已存的唯一子节点。没有后继的非空选择仍算一轮，不生成新结果。

rho 固定扫描 `0, .25, .5, .75, 1`。评分实现论文式 (1)：各世界自身的调用总数 B 与正最大质量 S 归一化，质量／调用 Pareto 超体积减去 λ 倍平均轮数／调用；零调用在平均中贡献零。所有历史世界等权比较，原策略保留，平分时保留较早版本。B 或 S 不满足论文前提时保存 collected-pool 并报告不可评分，不伪造优胜者，也不静默删掉不利世界。

可信策略在独立 Python 进程中执行，只通过 JSON 获得可见前缀；这不是 OS 沙箱，不防御蓄意读取历史文件的程序。开发者根据回放反馈改策略，部署策略自身不得读取未来记录、硬编码历史胜出 ID 或修改评价器。

## 验证范围

[协议检查案例](../../projects/dream-rsi-check/README.md)验证多层快照、独立执行评价、两轮策略选择与实际部署、池接续，以及离线零发现调用。它的自动 developer 是确定性夹具，不冒充模型；当前 Codex 的真实修订路径也保留单独证据。

算法实现的是论文第 3 节主循环，使用这里的 `select` 接口；没有照抄附录的网格 API，也没有复现九项科研基准或证明任意复刻任务的收益。这些范围不影响已实现的主循环可用性。消融仍只在完成复刻之后用于优化。
