# 框架发行与组织同步

源仓库的已提交Git对象拥有代码，`pyproject.toml`拥有版本号，CHANGELOG说明本版成果与限制。`scripts/package_framework.py`拥有发行范围和组织快照适配；它只生成文件，不创建Goal、推送仓库或发布Release。

## 生成快照

从已验证的源提交运行：

```sh
python3 -m scripts.package_framework --workspace . --ref HEAD --out private/framework-release-new
```

输出目录必须不存在。程序从Git对象读取文件，不读取未提交工作区改动。包含框架代码、方法文档、可独立运行的测试和`projects/dream-rsi-check`合成协议夹具；排除实际App案例、案例专用测试、私有输入、媒体和缓存。README与案例链接适配为纯框架发行范围，历史证据链接固定到源提交；不搬运私有证据。

包内`FRAMEWORK-SOURCE.json`记录源仓库、源提交、版本、适配文件和逐文件SHA-256。`capabilities/`、`runtime/`等运行代码应与源提交逐字节一致；文档适配与源码改动分别核对。

## 验证及发布

1. 在干净输出目录运行`python3 -m unittest discover -v`；核对本地文档链接和文件摘要。测试使用自建临时Git夹具，不要求发行包本身带`.git`。
2. 在组织仓库独立检出中应用这份快照，保留独立Git历史；不要合并个人仓库的App历史或复制整个工作区。检查远端差异及既有workflow，运行测试和`git diff --check`。
3. 经用户明确授权后，在两边创建同名版本标签及Release；从已验证快照制作框架专用压缩包，上传同一个二进制文件。根仓库的GitHub自动源码归档仍代表整个源码仓库，框架使用者应选专用发行包。
4. 核对远端提交、标签、Release版本、组织可见性及两边附件SHA-256。源提交与组织提交可以不同，框架快照与发行附件必须对应同一版。

实际发布回执由GitHub Release及其附件拥有，不在本文维护第二份发布状态。组织仓库范围见组织同步说明（归档证据未附带）。

## 私有源码与公开框架／样例

`whyy9527/rebuild-any-web` 是完整私有源码仓库；
`whyy9527/rebuild-any-web-framework` 是独立历史的公开仓库。
公开范围由同一个打包程序的 `--sample duolingo-swift` 选择：框架、通用测试、
合成 RSI 协议夹具，以及 Duolingo 的观察／契约入口和 Swift 客户端。
案例携带封存比较与第四课回放所需证据，以及项目配置中 JSON 输入传递引用的资源；不复制全部探索历史。Duolingo 早期实验的被引用证据保留原路径，但不导出该实验实现。
已删除案例的旧提交仅留在私有历史。

```sh
python3 -m scripts.package_framework --workspace . --ref HEAD \
  --sample duolingo-swift --public-repo whyy9527/rebuild-any-web-framework \
  --out private/public-framework-new
```

公开快照不合并源仓库历史，不创建源码仓库的 fork；执行脚本保留 Git 可执行位，
二进制资源按原字节导出。框架运行代码、Swift 源码与第三方素材的许可边界不变。
公开文档对未附带证据标注归档缺失，不把私有源文件链接当作公开下载入口。
发布前在快照运行完整 Python 测试、检查项目入口及 Swift 构建／核心检查，
核对文件摘要、文件范围和远端可见性。新版本仍通过显式快照更新，不能直接推送私有 main。
