# 第三方内容与许可范围

根目录 [MIT License](LICENSE) 授权本项目原创代码和文档。它不重新授权第三方作品、商标或服务，也不将网页可访问性解释为开源授权。

## Duolingo 案例

`projects/education-swift/Sources/LingoSeed/Resources/Reference/` 包含为比较原版体验采集的字体、图形、语音、音效和动画；`projects/duolingo-web/` 及历史实验的证据、契约和夹具也可能包含原版截图、录音、页面文字或课程内容。资源来源记录在案例资源清单和证据中。

这些第三方内容不属于本项目的 MIT 授权，权利归其原权利人。仓库未附带将 Duolingo 素材用于其他产品或再分发的授权；使用本项目原创工具的 MIT 许可不能代替这类授权。复用教育软件基座时应提供自己有权使用的内容和素材。

Duolingo 案例是已结束、未达到 1:1 的独立技术实践。Duolingo 名称及标识仅用于识别参考产品，不表示合作、官方客户端或背书。

## 依赖与研究来源

依赖由各自项目授权；安装依赖不会将其变为本项目的原创内容。当前案例引用：

| 项目 | 上游许可入口 | 用途 |
| --- | --- | --- |
| Rive iOS | [MIT](https://github.com/rive-app/rive-ios/blob/main/LICENSE) | Swift 动画运行时 |
| Lottie | [Apache-2.0](https://github.com/airbnb/lottie-spm/blob/main/LICENSE) | Swift 动画运行时 |
| Playwright | [Apache-2.0](https://github.com/microsoft/playwright/blob/main/LICENSE) | 框架可选浏览器采集与案例回放；browser extra 由 pyproject.toml 声明 |
| Pillow | [上游许可](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | 按需图像比较 |

锁定版本由案例的依赖清单管理，具体版本随附的许可与通知仍然适用。Dream-RSI、Cordis 的论文及实现来源保留在 [研究说明](docs/RESEARCH.md)；本仓库对它们的引用不改变原作者的权利，也不表示完整复现其算法。

浏览器采集的逐步证据与资源归属设计参考 [REA](https://github.com/morluto/rea)（[MIT](https://github.com/morluto/rea/blob/main/LICENSE)）。本仓库的 Python 实现独立编写，未包含 REA 源码或运行依赖；具体对应与差异由研究说明维护。框架包不捆绑 Playwright 或浏览器二进制，安装者使用依赖随附的上游许可。
