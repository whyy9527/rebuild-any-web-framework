# Swift 教育客户端

Duolingo 网页到 Swift 实践的 macOS 客户端。案例试验已结束，尚未 1:1；当前状态见 [Duolingo STATUS](../duolingo-web/STATUS.md)。本文件介绍模块和运行方式，不记录课程批次。

## 模块职责

- `LearningCore`：课程／题型内容、答题、重练、结算、偏好和进度持久化。
- `LingoSeed`：SwiftUI 客户端，`LearningModel` 连接 UI 操作、存储与媒体，原版字体／图形／Rive／Lottie 用于呈现。
- `LearningCoreChecks`：可执行业务检查入口；本包没有 `swift test` 测试 target。
- 浏览器／原生驱动与共同验收由相邻 `duolingo-web` 案例拥有，客户端不自行宣布复刻通过。

## 运行

需要 macOS 与 Swift 工具链。从仓库根使用案例清单：

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command build
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command launch --out artifacts/swift-review-new
python3 -m workflows.rebuild.project run --workspace . --project projects/duolingo-web/rebuild.json --command core
```

`launch` 使用刚构建的二进制；先 build，使用尚不存在的输出路径建立独立进度。进度文件和旁边的偏好文件属于本机运行数据，不提交到源码。直接 Swift 构建入口仍可使用：

```sh
swift build --package-path projects/education-swift --product LingoSeed
swift run --package-path projects/education-swift LearningCoreChecks
```

## UI 与模具

实际 UI 验收必须先构建，再驱动自有应用并核对二进制摘要。共同业务场景、前端契约、准备夹具及回放／比较命令由 [项目配置](../duolingo-web/rebuild.json)连接，具体用法见 [案例 README](../duolingo-web/README.md)。

课程实例来自实际观察，不表示完整服务端行为；可运行、核心检查通过、原资源播放或角色能动，都不单独证明复刻一致。可选课程／展示元数据保持兼容，新的基座接口应从实际消费者提取，避免把单次画面常数推广成业务规则。

结束时遗留的未完成翻译提示交互修改已按用户授权撤销，处理记录见 [案例状态](../duolingo-web/STATUS.md)。历史技术记录与旧完整 README 见 [历史索引](../../docs/history/README.md)。
