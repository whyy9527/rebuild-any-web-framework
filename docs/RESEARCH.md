# 方法来源与实现对应

本页记录原论文、借鉴的方法与实际实现的对应关系。日常复刻按 [Workflow](../workflows/rebuild/WORKFLOW.md)执行；历史研究记录保留在文末。

本仓库的 RSI 由 Codex 消费实际探索树的回放反馈，修订可执行策略，再将胜出策略部署到后续探针；发现进入 E2E。算法协议、复刻体验与研究基准分别验证。

## Dream-RSI

[Dream-RSI: Recursive Self-Improvement through Evolving Worlds](https://arxiv.org/abs/2609.14858v2)，Tong Zheng 等，2026。[官方仓库](https://github.com/zhengkid/Dream-RSI)。

原研究将历史发现树构造成回放模拟器，利用已记录结果评价和改进探索策略，再部署策略收集更多历史。本仓库现按论文第 3 节独立实现这一主循环，具体接口见 [RSI](../workflows/rebuild/RSI.md)。

| 已有实现 | 实际职责 |
| --- | --- |
| [树与回放算法](../capabilities/exploration/dream.py) | 多层父子树、前缀揭露、同一决策接口、rho 扫描、质量／成本／并行评分、全历史池比较与原策略保留 |
| [运行适配](../runtime/dream.py) | 父快照恢复、固定 agent／独立 evaluator、策略修订反馈、胜出源码及下一轮部署 |
| [Workflow](../workflows/rebuild/WORKFLOW.md)及[命令](../workflows/rebuild/dream.py) | 当前 Codex 直接读取反馈并写策略，或显式配置 developer 命令，连接 collect/replay/cycle |
| [探索前沿](../capabilities/rebuild/discovery.py) | 从真实记录列出尚未完成的状态／动作／输入方式；不自行优化策略 |
| 历史回放（归档证据未附带） | 保留的早期单层实验，不是新引擎 |
| 策略部署（归档证据未附带） | 模型利用真实反馈修订策略，再实际操作原版，将发现交给模具与 Swift |

主循环的实现检查见 [验证记录](../projects/dream-rsi-check/VERIFICATION.md)及[测试](../tests/rebuild/test_dream.py)。此前实现缺少上述核心机制，这次补的是运行算法，不只是改称呼。官方仓库核对时只有论文及说明、尚未发布实现源码，因此这是依据论文的独立实现；没有声称复现附录全部工程设置或九项科研基准。回放分数也不保证新任务收益或原版需求已完整发现。

## Cordis

[A Programming Paradigm for Spatiotemporal Composability](https://arxiv.org/abs/2608.25512v1)，Yifan Shi、Wei Zhang、Tianyi Cui，2026。[实现](https://github.com/cordiverse/cordis)。

原研究以可撤销副作用和响应式依赖管理实现动态组件的空间／时间组合。它为本仓库的职责分离与资源生命周期提供设计参考：能力、宿主运行时和工作流各有所有者；[命令运行器](../runtime/runner.py)负责自己启动的进程组清理，具体职责见 [架构](ARCHITECTURE.md)。

当前借鉴停留在设计层。运行链没有导入 Cordis，也没有实现其 context、可撤销副作用或响应式依赖机制；普通模块分层和进程清理不能称为 Cordis 核心机制的复现。

## REA 浏览器采集

[REA: Reverse Engineer Anything](https://github.com/morluto/rea)，本次研究固定到提交 [47b4628](https://github.com/morluto/rea/tree/47b4628bac7300e5486dd6018663b1cc5dfbf01c)。阅读了场景采集、artifact、就绪动作、网络事务及 launch/connect 清理实现和相关测试；本仓库未导入其源码或依赖。

借鉴的是逐步证据、显式漏采、资源归属及比较前的完整性检查。独立实现见[采集运行时](../runtime/browser.py)、[证据门禁](../capabilities/rebuild/browser.py)及[CLI](../workflows/rebuild/browser.py)，沿用原 RSI 和共同前端模具。REA 的场景截图关闭动画、环境默认减少动效和阻止 Service Worker；本实现选择保留动画与光标、允许 Service Worker，连接模式测量已有页面环境。

本实现用显式就绪及采集前后状态防止旧结果与跨状态误判，仍不保证原子截图、完整动态媒体或需求全集。真实合成站点验证见[浏览器测试](../tests/rebuild/test_browser_live.py)，运行方式和边界见[采集指南](BROWSER-CAPTURE.md)。REA 的义务台账与 MCP 未引入；不以其字段或工具数量判定本仓库自主复刻能力。

## 实践与历史实验

| 记录 | 保留的事实与用途 |
| --- | --- |
| [Duolingo 经验](DUOLINGO-LESSONS.md) | 真实遗漏、策略／观察方法调整，以及模具和实现如何消费发现；直接用于改进 repo |
| 真实策略部署05／06（归档证据未附带） | 真实模型利用反馈改变探索动作，实际发现页面内容并进入共同契约和 Swift |
| 探索04（归档证据未附带） | 两组语义代理新增0／0；后续焦点探针揭示该指标漏掉前端要求 |
| 探索02／03（归档证据未附带） | 实际策略与部署记录；起点／采样问题使比较不可判定 |
| 前端反馈质量消融（归档证据未附带） | 两组40／40，图像仍不同，有反馈组没有额外改善；揭示控件指标饱和和样本拟合问题 |
| 业务四组消融（归档证据未附带） | 已有共享业务场景结果无通过率差异；保留成本、失败和限制 |
| 模型多阶段接续（归档证据未附带） | 旧 Hook/Pipeline 的实际宿主执行与恢复证据，供兼容模式参考 |

这些历史结果保持原结论。当前流程先完成复刻和完整验收，消融留到完成后的优化阶段，比较机制对质量、成本和耗时的影响；顺序由 [Workflow](../workflows/rebuild/WORKFLOW.md)维护。默认复刻 Goal 依据用户体验与模具验收完成。

更早的源码与原始研究报告保存在提交 `2ad5175`：

```sh
git show 2ad5175:projects/paper-v2/REPORT.md
git show 2ad5175:projects/paper-v3/REPORT.md
git show 2ad5175:projects/self-improvement/REPORT.md
```

旧报告中的24实例无算法收益与模型预检失败继续保留。整理前的详细研究记录及批次说明可从 [历史索引](history/README.md)查找，不把旧命令冒充当前运行接口。
