# Duolingo 网页到 Swift 案例

本案例形成了 rebuild 的实际探索和模具经验：中文母语学习英语、网页原版到 macOS SwiftUI。试验已结束，1:1 未完成；已验证结果与缺口见 [STATUS](STATUS.md)，经验见 [复盘](../../docs/DUOLINGO-LESSONS.md)。

当前输入和命令统一由 [rebuild.json](rebuild.json)连接。主 README 不再追逐契约版本或追加课程批次，历史与旧入口见 [历史索引](../../docs/history/README.md)。

## 读取目标与证据

从仓库根执行，需要 Python 3.11+：

```sh
python3 -m workflows.rebuild.project status --workspace . --project projects/duolingo-web/rebuild.json
python3 -m workflows.rebuild.project goal --workspace . --project projects/duolingo-web/rebuild.json
```

两条命令只读项目，第二条输出原生 `create_goal` 参数，不创建或恢复任务。只有用户要求重新开始案例时，当前 Codex 才按 [工作流](../../workflows/rebuild/WORKFLOW.md)使用它。

## 构建和查看 Swift

需要 macOS、Swift 工具链。使用新进度路径隔离查看状态：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command build
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command launch --out artifacts/duolingo-review-new
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command core
```

核心检查不替代实际 UI、画面或声音验收。Swift 模块与构建边界见 [客户端](../education-swift/README.md)。

## 复跑封存课程及严格比较

实际原生回放需要辅助功能／截图权限，驱动只操作自己启动的应用。`replay` 先构建，再按封存准备夹具执行第四课完整旅程；并非整站或最新线上原版验收。以下输出目录必须尚不存在：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command replay --out artifacts/duolingo-replay-new
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command compare --observed artifacts/duolingo-replay-new/observed.json --out artifacts/duolingo-compare-new
```

当前严格比较预期返回1并保存 fail 回执；不能吞掉退出码或把旧通过当当前完成。只查看命令可加 `--dry-run`。最新已提交 [修复证据](evidence/english-frontend-repair-v80/README.md)保留源码／二进制摘要、实际图像、声音和失败；查看该记录不会自动重启试验。

## 原版与协议

浏览器观察需要 Node.js、Playwright 和原版网络；依赖在本目录 `package.json` 中，首次使用安装相应浏览器。已有 `original-adapter.mjs` 与早期 `spec-v2.json`／`targets-v2.json` 供历史共享业务场景复跑，它们允许语义对应而非相同题库，不能作为当前 1:1 完成标准。

线上访客、服务端进度、自适应题目、跨日状态不能靠刷新完全重置。使用证据中的明确准备路径和实例，保留限制；不要混用新访客与课后状态。具体平台协议见 [BEHAVIOR-CONTRACT](../../docs/BEHAVIOR-CONTRACT.md)，项目入口格式见 [PROJECT](../../workflows/rebuild/PROJECT.md)。
