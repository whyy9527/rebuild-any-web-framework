# 框架发行

`whyy9527/rebuild-any-web` 是私有框架源仓库，
`whyy9527/rebuild-any-web-framework` 是独立历史的公开框架仓库。
已提交 Git 对象拥有代码，`pyproject.toml` 拥有版本，CHANGELOG 记录成果与限制。
`scripts/package_framework.py` 只生成受控快照；App 实现由独立消费仓库维护。

## 生成与验证

按[环境说明](ENVIRONMENT.md)准备锁定环境并验证源提交。从仓库根生成新目录：

```sh
python3 -m scripts.package_framework --workspace . --ref HEAD \
  --public-repo whyy9527/rebuild-any-web-framework \
  --out private/public-framework-new
```

输出只包含框架、方法文档、通用测试与合成 Dream-RSI 协议夹具。
App 样例模式已退役；不读取私有输入、旧案例源码、原版媒体或历史实验目录。
快照从 Git 对象生成，忽略未提交工作区；二进制和执行位按声明范围保留。

`FRAMEWORK-SOURCE.json` 记录源提交、版本、适配文件与逐文件 SHA-256。
运行代码与源提交逐字节相同，文档适配单独核对。
在干净快照运行完整 Python 测试与真实无头浏览器检查，核对本地文档链接、
摘要及 `projects/` 只含协议夹具。公开包不再执行或捆绑 Swift 客户端。

## 同步与发布

1. fetch 公开仓库，检查差异、工作流与本机未提交内容。
2. 按快照 manifest 更新受管文件，并删除上一快照中已退役的文件；保留独立 Git
   历史及不属于快照的本机内容。不得将私有源仓历史直接推到公开仓库。
3. 核对摘要和 `git diff --check`，提交、推送并确认远端提交。
4. 用户授权发行后，在源仓和公开仓库发布同名标签与 Release，将同一个已验证
   框架压缩包及 SHA256SUMS 上传两边。源码仓自动归档包含其完整范围，框架下载选专用附件。
5. 下载两边附件，核对版本、标签提交、仓库可见性与 SHA-256。

当前分发取消样例不重写旧标签或 Release；旧版属于历史记录。
历史案例的完整私有恢复入口见[退役索引](history/retirement-2026-10-22.md)。
实际发布回执由 GitHub Release 和附件拥有，本文不维护第二套运行状态。
