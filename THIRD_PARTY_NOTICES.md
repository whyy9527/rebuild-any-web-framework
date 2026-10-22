# 第三方内容与许可范围

根目录 [MIT License](LICENSE) 授权原创代码和文档，不重新授权第三方作品、商标或服务。
网页可访问性不等于开源或再分发授权。

## 当前框架

框架只附带通用工具、文档、测试和合成协议夹具，不包含 App 客户端、Duolingo
字体／图形／录音／动画、网站私有媒体或模型权重。历史素材及其原始通知保留在
Git 历史，权限和权利归属不因当前删除而改变；恢复入口见[退役索引](docs/history/retirement-2026-10-22.md)。

| 依赖 | 上游许可 | 用途 |
| --- | --- | --- |
| Playwright | [Apache-2.0](https://github.com/microsoft/playwright/blob/main/LICENSE) | 可选浏览器采集；browser extra |
| Pillow | [上游许可](https://github.com/python-pillow/Pillow/blob/main/LICENSE) | 可选图像比较；images extra |

依赖及其传递包遵循各自随附许可，维护版本和发行文件哈希见 `requirements.lock`。
框架包不捆绑浏览器二进制、Swift 动画运行库或第三方 App 素材。

## 独立应用与历史

瓦站、S16 与方块杀手的当前代码、资源通知和部署维护由各自独立仓库拥有。
第三方字体、游戏标识及上游发布代码仍遵循原通知；本仓 MIT 不代替这些授权。
Duolingo 历史案例已结束且未达 1:1，名称仅用于识别研究对象，不表示官方客户端或背书。

Dream-RSI、Cordis 的来源与实现边界由[研究说明](docs/RESEARCH.md)维护。
浏览器逐步证据与归属设计参考 [REA](https://github.com/morluto/rea)
（[MIT](https://github.com/morluto/rea/blob/main/LICENSE)）；框架为独立 Python 实现，
未导入其源码或运行依赖。引用不改变原作者权利，也不表示完整复现。
