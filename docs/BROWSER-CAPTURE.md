# 浏览器采集 CLI

采集器实际执行浏览器动作，保存逐步事实；RSI 使用这些事实选择下一步，已有前端 E2E 模具负责验收。采集成功不表示复刻完成，也不自动生成业务要求。实现参考 REA 的逐步记录与漏采表达，未导入 REA。

## 安装与运行

需要 Python 3.11+ 与调用者已安装的 Chromium 系浏览器。浏览器依赖按需安装；基础框架不要求 Playwright。开发与发行复验使用[锁定环境](ENVIRONMENT.md)，像素比较另需 images extra。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install '.[browser,images]'
.venv/bin/python -m workflows.rebuild.browser --workspace . --scenario browser.json --out artifacts/browser-new
```

`--scenario` 和 `--out` 相对显式 workspace。输出目录必须不存在；复跑换一个目录，不覆盖失败证据。CLI 退出码：0 为请求的观察已采到、采样状态稳定且资源释放成功；1 为不完整观察；2 为输入或依赖错误。没有产品验收 pass。

最小 `browser.json`：

```json
{
  "schema_version": 1,
  "browser": {"mode": "launch", "executable": "/path/to/chromium"},
  "start_url": "http://127.0.0.1:3000/",
  "viewport": {"width": 800, "height": 600},
  "timeout_ms": 10000,
  "elements": {"search": "#search", "result": "#result"},
  "steps": [
    {
      "id": "result",
      "action": {"type": "click", "selector": "#search"},
      "ready": {"selector": "#result[data-version='new']", "state": "visible"},
      "capture": ["dom", "screenshot", "accessibility", "text"]
    }
  ]
}
```

示例的 `data-version` 由应用在当前结果返回后设置。Codex 必须先观察原版，选择能排除旧结果的就绪条件；标题、旧结果容器可见或 `load` 事件都不能自动代表业务就绪。`ready` 必填，状态可为 visible、hidden、attached、detached。按步骤分别记录动作执行与就绪结果。

动作固定为 `observe`、`click`、`fill`、`press`、`hover`、`scroll`、`goto`：

| 动作 | 字段 |
| --- | --- |
| observe | 无；观察当前状态 |
| click / hover | selector |
| fill | selector、value（字符串，可为空） |
| press | selector、key，例如 Enter、Tab |
| scroll | x、y（实际滚动位置另行测量） |
| goto | url（HTTP(S)） |

动作定位遵循 Playwright 的严格匹配；`elements` 是需要读取值、角色、启用状态及矩形的具名 CSS 选择器，重复匹配会报告采集错误。跨原版／候选使用相同逻辑名，选择器可不同。角色读取只支持显式 ARIA 与常见原生控件，未识别角色保持 null。

## 连接已有登录会话

`browser` 换为下面的结构，并移除 `start_url`、`viewport`：

```json
{
  "mode": "connect",
  "endpoint": "http://127.0.0.1:9222",
  "target_url": "https://example.test/current-page"
}
```

CDP 地址必须为带显式端口的 loopback origin；`target_url` 必须唯一匹配一张已有页面。采集器不任选标签页、不创建替代页、不改其视口；导航和其它修改由场景动作明确指定。连接模式会操作选定页面并保留它的最终状态；结束时断开本次连接，外部浏览器继续存在。launch 模式使用隔离上下文，结束时关闭自有浏览器。

浏览器启动不安装或升级浏览器，不复制登录凭证、不恢复远端业务状态。输出会保存选定页面的真实内容，是否保留或提交这些内容由消费项目的授权范围决定。

## 证据与前端模具

每一步生成 `NNNN-step.json`、所选 artifact 文件。总入口为 `observed.json`，其中 `states` 可直接传给现有 `capabilities.rebuild.frontend`。步骤 ID 同时是前端状态 ID。

- `requested` 保存本次选择。每种 artifact 分为 captured、not_requested、unavailable；captured 含相对路径、SHA-256 和实际字节数。PNG 另存实际头部尺寸。
- `before`／`after` 保存文档身份、DOM 变化序号、实际 URL、视口、设备比例、语言、时区、配色、减少动效设置、Service Worker 控制状态、滚动、焦点、悬停链及具名元素事实。
- 动作后先等待显式 ready，再观察连续帧的准备状态，随后采集。采集期间发生变化会保留两份状态与原文件，结果为 incomplete。没有自动重采并挑选有利结果。
- 截图保留 CSS 动画和输入光标；启动允许 Service Worker，使用 no-preference 动效设置。已有会话的实际环境直接测量。
- 动作或 ready 失败后，后续步骤为 not_run；部分 artifact 失败保留其它已采文件；清理失败另行记录。

给现有 requirement 加上 `browser_capture` 后，候选必须提供相应浏览器步骤证据：

```json
{
  "id": "result-text",
  "state": "result",
  "kind": "accessible_text",
  "text": "New result",
  "evidence": ["artifacts/reference/0000-step.json"],
  "browser_capture": {
    "reference": "artifacts/reference/0000-step.json",
    "required": ["dom", "text", "screenshot"]
  }
}
```

比较器先核验两端步骤身份、动作、ready、清理、采样稳定性与文件摘要，再比较共同准备条件（环境、滚动、焦点、悬停）。所有已请求 artifact 都必须采集成功；required 中未请求的 artifact 也不能算通过。原版实际证据须先满足同一条已有断言，随后才对候选执行该断言。候选的文字、元素与图像引用必须对应其证据，不能靠手改 `states` 或驱动 pass 绕过。

`image_pixels` 同时声明原版实际 PNG、`pixels` 和 `reference_capture`（从原版 observed 的 capture 读取）；候选 capture 仍走现有 ICC、实测缩放及严格像素比较。`capture_dimensions` 从实际 PNG 尺寸核验。其它维度不能替代图像验收。

没有 `browser_capture` 的既有原生契约保持原语义。浏览器门禁目前不接受 `relative_to_state`：它还需要独立核验原点证据，不将未验证原点混入本次比较。

## 在 RSI 和项目入口中使用

项目现有命令可引用此 CLI，例如给 `rebuild.json` 的 `commands` 增加：

```json
{
  "capture": ["python3", "-m", "workflows.rebuild.browser", "--workspace", ".", "--scenario", "browser.json", "--out", "{out}"]
}
```

通过 `project run --command capture --out artifacts/capture-new` 调用。模块需要能从所选 Python 环境导入；安装 browser extra 后可在消费工作区执行。RSI 的 agent 可在自己的独立 workspace 调用同一采集 CLI，并把 receipt 作为实际 observation；evaluator 仍独立消费共同模具，采集器不接收 expect、不选择探索策略、不管理 Goal。恢复本地快照不等于恢复线上会话或服务端业务状态。

## 验证与边界

```sh
python3 -m unittest tests.rebuild.test_browser -v
REBUILD_BROWSER_EXECUTABLE=/path/to/chromium python3 -m unittest tests.rebuild.test_browser_live -v
```

真实验证使用自有临时 HTTP 站点，覆盖旧结果／延迟返回、故意错误候选、字体等待导致截图失败、DOM 采集漂移、输入／焦点／悬停／滚动、动效保留、Service Worker 与连接清理。未提供浏览器及依赖时，live suite 明确 skip；普通单元测试通过不代表真实浏览器验证已执行。

采集是可信本地工具协议，不是防伪认证。采样稳定不证明多种 artifact 在同一瞬间取得，也不证明 CSS／Canvas 动画时序一致。当前不采网络正文、音频、视频或跨框架 DOM／Shadow DOM 的完整语义；主文档 DOM 与具名控件不能代表需求全集。iframe、Canvas 与动态效果仍需 Codex 选择对应探针和模具。显式 ready 条件也不能证明所有后台工作结束。
