# 验证环境

框架支持 Python 3.11+。基础模块只用标准库；浏览器采集的 `browser` extra
声明 Playwright，像素比较的 `images` extra 声明 Pillow。缺少相应依赖的
能力仍报告 unavailable，不能把被跳过的检查计为通过。

维护和发行使用根目录 `requirements.lock`，它固定两个 extra 的传递依赖
及发行文件 SHA-256。消费安装可按需选择 extra；维护复验按锁文件新建环境：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m unittest discover -v
REBUILD_BROWSER_EXECUTABLE=/path/to/chromium .venv/bin/python -m unittest tests.rebuild.test_browser_live -v
```

在仓库根验证时不需要安装本包。需要从其他消费目录调用 CLI 时，可使用
`.venv/bin/python -m pip install --no-deps .`；构建工具由 pyproject.toml 声明，
不属于运行依赖锁。运行时不借用系统 site-packages。仓库验证使用上述同一
环境及模块入口。

浏览器是显式输入，由调用者设置真实可执行文件路径。需要复现锁定的 Playwright
配套浏览器时，在此环境执行 `.venv/bin/python -m playwright install chromium`，
再用 `sync_playwright().chromium.executable_path` 取得路径传给上述环境变量。
这只安装配套浏览器，不自动升级调用者的系统浏览器。所有自动验证无头运行；
采集回执记录浏览器版本。锁文件不捆绑浏览器、模型或权重，不承诺不同浏览器
版本的截图相同。Swift 样例的依赖由其 `Package.swift` 与
`Package.resolved` 管理，构建及业务检查见[客户端入口](../projects/education-swift/README.md)。

只有需要升级依赖时才重新生成锁文件（生成器不是运行依赖）：

```sh
uv pip compile pyproject.toml --extra browser --extra images --universal --generate-hashes --no-emit-index-url --output-file requirements.lock
```

审查版本与哈希变化后，在新的虚拟环境重新安装并执行完整测试及真实无头浏览器检查。
