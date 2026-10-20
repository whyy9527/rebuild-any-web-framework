# 宝箱、排行榜遮罩与下一Practice入口

2026-10-11。接续默认第八课（归档证据未附带）。上一轮是有效进展，本轮按frontier选择原版可打开宝箱，而非重复重练碰未知题。完整Goal仍active，原始Dream-RSI/Cordis及既有负消融见[RESEARCH](../../../../docs/RESEARCH.md)；没有新增RSI收益或声学结论。

## 原版实际分支

恢复真实会话后仍在/learn，两Lesson已完成、宝箱可打开，宝石510。首次宝箱click实际超时：可见/可用，但排行榜已解锁遮罩截获指针。保存`before`、`opened`的当地捕获；归档中的`before`和`after-escape`保留画面。Escape没有关闭遮罩。失败click的自动scroll令后续after-escape中的路径上移，不是新路径布局；不能把这张图套到初始状态。

DOM确认遮罩为全视口DIV，正常点击遮罩后提示消失（`dismissed`），再次正常点击宝箱成功。没有force、修改网页状态或绕过覆盖层。开箱后宝石525、宝箱禁用并换已打开SVG、Practice激活（`after-click`）。真正reload后525和已打开状态保留（`reloaded`），未再次领取。**本实例变化15，不推广为所有宝箱公式。**

下一Practice弹层显示“第1/2单元”“开始 +10 经验”，实际链接/lesson；点击后实际出现“来创建你的个人档案吧！”及“稍后创建帐户”。选择稍后后返回/learn，开箱状态和525保留；源结束于该主页。未创建账号，后续题单未观察。这个入口已可正常到达，却仍弹建档，不能据链接猜测正常课程题型或把八课标整部分完成。

## 模具、实现及前端失败

`freeze-chest.py`在候选修改前冻结v39：保留2321旧项追加34，共2355，含遮罩、开箱、刷新、下一节点的真实状态。v13保持八课115题原样，只加第八课后主页快照及此宝箱实例的源素材/几何/宝石端点。

最初冻结遗漏下一Practice开始控件的角色/enabled，只检查了文案；这是模具盲点。v40保留全部v39，补开始链接3项及同状态文案/整图共6，总2361。实际候选开始按钮不可用，因此明确失败；没有用文案通过掩盖。继续实际点击源Start发现建档提示，v41再保留全部旧项追加12，共2373，冻结提示两按钮、文案、关闭返回和整图；**候选这12项全部not_run，尚未实施**。源v41自检560pass/0fail/1799not_run/14unavailable。

LearningProgress新增按courseID隔离的openedPathChests，只有源夹具列出的八课完成才可开；重复开不重复变更。旧存档缺字段仍可读。LearningModel保存实际开箱动作；ReferenceHome使用源80×90素材、源中心和开箱前后快照，525从该实例的afterGems读取，不按课程数加钱。开箱不设置completedCourses；下一Practice仍有未编译单元。

第一轮原生5状态完成真实click/进程重启/下一弹层，但AX宝箱80×80、素材被旧导入器180方形画布缩小。两份原SVG实际width80/height90，导入器增加可选render_width/render_height；旧资源仍默认180方形。新素材按80×90在独立浏览器context渲染，实际PNG240×270和源SVG SHA全部核验。原生控件改为已有NSButton适配，保持80×90的独立命中/AX边界。仅在源实际几何上修改，未放宽容差。

最终6状态无驱动失败，实际从510可开→525禁用→真实进程重启仍525/禁用，保存courseID/chestID。源y324.2265625，原生y324，**0.2265625点仍fail**；开始控件几何、角色及enabled仍fail。共同v41本轨迹34pass/17fail/2322not_run，baseline32pass/13fail/2328not_run，访问状态不同，不能拿数量增加当质量收益。开箱整图RGB差约[4.68,3.47,6.66]→[4.49,3.09,5.65]，仍fail。排行榜遮罩尚未实施；动画、角色、字体、其它主页和声音均有剩余差异。

同一最终二进制默认第八课41状态回归无驱动失败，共同v41为133pass/17fail/2223not_run。构建、29核心（锁定/一次性/恢复/旧存档兼容）、56Python、14Node通过。两种资源管线的原始回执和失败截图保留，baseline方形PNG已被重生成，不声称当前文件仍匹配baseline旧render哈希；final两份PNG/SVG逐项核验。不存在本批新的模型消融、实际声音或探索充分结论。

## 复跑

```sh
python3 projects/duolingo-web/freeze-chest.py --out-dir artifacts/chest-freeze-new
python3 projects/duolingo-web/freeze-chest-start.py --out-dir artifacts/chest-start-freeze-new
python3 projects/duolingo-web/freeze-practice-profile.py --out-dir artifacts/chest-profile-freeze-new
swift build --package-path projects/education-swift
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest discover -v
node --test projects/duolingo-web/*.test.mjs
swift projects/duolingo-web/observe-frontend.swift artifacts/chest-native-new projects/duolingo-web/fixture-reference-en-zh-v13.json --seed-progress projects/duolingo-web/evidence/english-chest-v1/progress-seed.json --reference-color-scheme light --exercise-path-chest
python3 projects/duolingo-web/sample-frontend-colors.py --contract projects/duolingo-web/frontend-english-v41.json --observed artifacts/chest-native-new/observed.json --out artifacts/chest-native-new/observed-colors.json
python3 -m capabilities.rebuild.frontend --contract projects/duolingo-web/frontend-english-v41.json --observed artifacts/chest-native-new/observed-colors.json --out artifacts/chest-native-new/validation.json
```

共同seed是已映射主课八课进度，未含开箱记录；原版账号没有被重置或读隐私状态。驱动每次使用新输出目录，原生运行顺序执行。下一批按frontier（归档证据未附带）补实际建档提示、排行榜遮罩与其正常交互，修前端/声音，再继续下一课程入口。不能把disabled候选Start当正常原版行为。逐状态失败、二进制与未知见verification-summary（归档证据未附带）；图片保持原字节，`sha256-manifest.json`记录摘要。
