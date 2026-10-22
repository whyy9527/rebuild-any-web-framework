# 框架发行

`whyy9527/rebuild-any-web` 是私有框架与案例历史源仓库，`whyy9527/rebuild-any-web-framework`
是独立历史的公开框架与 Duolingo Swift 样例仓库。源仓库已提交 Git 对象拥有代码，
`pyproject.toml` 拥有版本号，CHANGELOG 说明成果与限制。
`scripts/package_framework.py` 拥有发行范围和文档适配，只生成文件。

瓦网站和 S16 网站由 `xinxiayiyan` 下各自的私有仓库维护，不进入框架发行。
旧组织镜像不作为本轮发行目标；不得将私有源码历史合并进公开仓库。

## 生成与验证

先按[环境说明](ENVIRONMENT.md)安装锁定依赖并验证源提交。从仓库根生成新目录：

```sh
python3 -m scripts.package_framework --workspace . --ref HEAD \
  --sample duolingo-swift --public-repo whyy9527/rebuild-any-web-framework \
  --out private/public-framework-new
```

不带 `--sample` 时只输出框架与合成 Dream-RSI 协议夹具。程序从 Git 对象读取，
不发布未提交工作区。样例携带封存比较与第四课回放所需证据，以及配置 JSON
传递引用的资源；不搬运全部探索历史、其他 App、私有输入、缓存或权重。
二进制资源和执行位保留，公开文档对未附带证据标明归档缺失。

包内 `FRAMEWORK-SOURCE.json` 记录源提交、版本、适配文件和逐文件 SHA-256。
运行代码及 Swift 源码应与源提交逐字节相同；文档适配单独核对。
在输出目录运行完整 Python 测试及真实无头浏览器测试，检查本地文档链接、
摘要和文件范围。公开样例另运行 Swift 构建及 `LearningCoreChecks`。
第三方许可边界不随快照改变。

## 同步与发布

1. fetch 公开仓库，检查差异、已有工作流和本地未提交内容。
2. 用已验证快照更新其受管文件，删除上版快照已退役的文件；保留独立 Git 历史
   和不属于快照的本地内容。不要直接推送私有 main。
3. 再核对快照摘要和 `git diff --check`，提交、推送并验证远端提交。
4. 用户明确授权发行后，在源仓库与公开仓库创建同名版本标签及 Release。
   框架专用压缩包从同一已验证快照生成，上传同一个二进制文件；根仓库自动
   源码归档含完整源范围，框架使用者应选择专用附件。
5. 下载两边 Release 附件，核对标签提交、版本、仓库可见性和 SHA-256。

源提交与公开提交可以不同；快照和发行附件必须对应同一版。
实际发布回执由 GitHub Release 及附件拥有，本文不记录另一套发布状态。
