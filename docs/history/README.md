# 历史索引

本目录与案例 evidence 保存过程记录。历史中的“下一批”“Goal active”“待做消融”等表述属于当时状态，不是当前运行指令。Duolingo 试验已结束，代码与实验已退役，原始范围见[退役索引](retirement-2026-10-22.md)。

## 整理前的主文档

本轮整理以前的完整 README、AGENTS、哲学、架构、Roadmap、研究说明和工作流仅保存在私有源仓库的提交 `80d4d77`。以下命令只能从具备权限的 `whyy9527/rebuild-any-web` 源仓检出执行；公开框架有独立 Git 历史，不包含这些提交：

```sh
git show 80d4d77:README.md
git show 80d4d77:docs/ARCHITECTURE.md
git show 80d4d77:docs/ROADMAP.md
git show 80d4d77:docs/RESEARCH.md
git show 80d4d77:workflows/rebuild/WORKFLOW.md
git show 80d4d77:projects/duolingo-web/README.md
git show 80d4d77:projects/education-swift/README.md
```

[旧 README 检查点](README-checkpoints-2026-10-12.md)和 [旧案例 README 检查点](duolingo-README-checkpoints-2026-10-12.md)继续保留。主文档现已按职责重写，新进展写进案例记录或独立运行证据，不再追加到这些主文档。

## 案例与实验

- [2026-10-22 案例与实验退役](retirement-2026-10-22.md)：删除范围、六组实验结论和冻结 Git 恢复入口。

- [2026-10-22 仓库治理](governance-2026-10-22.md)：网站独立、真实依赖解除及验证环境。

- [Duolingo 经验复盘](../DUOLINGO-LESSONS.md)：本轮改进来源与范围。
- [工作流整理与验证](rebuild-workflow-consolidation-2026-10-12.md)：目标模板、项目入口和封存比较接线。
- [早期交付审计](../DELIVERY-AUDIT.md)、[早期失败复盘](../REBUILD-RETROSPECTIVE-2026-10-10.md)：保留当时事实。
- 封存前端批次（历史证据未随公开发行）：最新已提交严格结果及原始证据。
- [研究来源](../RESEARCH.md)：原论文和实验入口；原始报告不改写。

更早研究源码与报告保存在 `2ad5175`，恢复方法见研究说明。只有私有源仓的冻结 Git 历史保留原始文档与案例 evidence 的原路径；当前源码树和纯框架公开包均不保留这些案例路径。
