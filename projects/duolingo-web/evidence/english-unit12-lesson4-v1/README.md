# Unit12 第四课：探索与前端模具继续补漏

原版实际完成17道计分题、1道口语跳过、挑战说明、成绩单、神射手成就升级、档案提示并回到Lesson5of6主页。当前155宝石/5红心是独立观察到的状态，未推断此前505→155的原因。原版接受的答案来自实际点击/键入及反馈，编译器不读取未来答案。

[真实源轨迹](source)、[共同夹具](../../fixture-reference-en-zh-unit12-lesson4-v1.json)、[实际原生场景](journey.json)、[并排画面](comparison.html)、[严格逐项结果](frontend-v79-delivery.json)、[失败聚合](failure-breakdown.json)、[检查回执](validation.json)。原生交付构建48状态、0驱动失败；38核心、67Python、26Node通过。前端v79共26779项：921pass/717fail/24058not_run/1083unavailable，整体fail。不能宣称1:1完成。

## 这次发现的遗漏

- 同一听力题可以切换键盘；空输入检查禁用，填入后启用，提交接受two bathrooms。下一道翻译保留键盘偏好，再切词库。模式、控件和状态分别冻结。
- 第四课结算插入“神射手成就等级已提升”，第3级；不能沿用第三课补心顺序。Swift使用原版成就SVG与实测布局。
- 原版OSCAR/VIKRAM当前角色与实际Rive缓冲区相绑定。下载公开原文件解压后与实际渲染缓冲区SHA相同，原生使用原状态机和变换；这只证明素材归属，不证明姿态/时序/像素等价。
- 主页Lesson5of6原版进度环有实际弧段。保留原路径、实测CSS变量填充及变换后的98×92.708几何，替换这一已观察状态的通用灰环；其它环状态继续待验证。
- 第四课后公寓电台仍未解锁；其正文尚未探索。第五/六课及上游技能、小故事独立入口继续进入探索队列。

## 模具自己的失败也必须记录

[原始主页截图](source/home-after.png)尺寸正确，DOM也稳定，却从文档顶部裁剪，和当前滚动视口不同。严格比较后人工查实际图像与独立CDP坐标发现此问题：原版pageY679.5，旧clip原点0。修复使用实测CSS文档pageX/pageY，[同进度重置回执](source/home-reference-reset.json)、[重采主页](source/home-after-fixed.json)保留原点679.5与实际PNG。旧参考保留为pending及嵌套原图断言，没有删除或放宽断言。

另一处角色截图调用让实际视口1200×732变为1192×705，虽然ARIA相同。`q10-closed`被新视口一致性门禁拒绝；保留失败，不能拿它验图。角色缓冲区增加不截页面的采集模式，真实12帧VIKRAM采集后页面视口保持稳定。采集器保存配置视口和实际DOM视口，原生观察器按显式测量的1192×705配置内容区。

规范控件库存遗漏TEXTAREA：旧visible记录实际上已保存textarea几何，v79对此单独验证；但旧actions/value库存未采齐，不能回填为新版库存。采集器已加入textarea/value，原版相同状态的完整新库存仍待重采。实际输入回执和ARIA值继续保留。新回归使用真实视口变化及滚动主页证据，不用造数据证明原版。

v79逐项保留v78的23444项，当前260状态/128实际边。前沿数量不当完成率。10张旧捕获缺视口前后身份，另有滚动原点错误，均保留不可比较记录。[参考审计](reference-image-audit.json)。原版/原生的档案页、共享题面/反馈、角色及听力控件仍有实际视觉差异，继续修复。

## 实际音频与执行失败

`native-first`32状态，AXPress没有实际切换键盘，随后找不到输入框；原失败保留。`native-final`48状态改用真实鼠标点击并验证输入/偏好，之后交付构建加入原版进度环，再完整跑48状态，音频动作发生在自有PID录音内，麦克风关闭。

[VIKRAM实际语音](q12-original-speech-measurement.json)与原资源拟合相关性0.999756、增益0.999572；[正确反馈](q12-original-correct-measurement.json)相关性0.999858、增益0.349951，和原版play回执音量0.35对应。记录的是原资源实际出现及拟合结果，未采原浏览器声学输出，不是全部声音/延迟/混音等价，更不是RSI消融。

`frontend-v79.json`是早期诊断，配套`frontend-v79-initial-contract.json`包含当时尚未发现的滚动裁剪错误，不能作为质量收益基线。最终结果使用新版审计和重采主页。源/原生归档摘要分别保存；文本仅归一化本机路径/EOF与声明的状态别名，PNG/Rive/WAV字节不变。

## RSI与下一步

[探索反馈](exploration-feedback.json)把实际遗漏、证据、修复和下一次探索连接起来。本批由主代理沿前序反馈实际探索，不能声称独立测得RSI收益；历史真实模型deployment05/06和04负结果不变。原始Dream-RSI/Cordis论文及机制边界仍见[研究说明](../../../../docs/RESEARCH.md)。真实匹配预算产品质量消融尚未完成。

下一批优先消费[真实图像失败](failure-breakdown.json)，修共享题面/反馈/档案页、缺失角色和慢速播放控件，同时继续未探索的故事/电台依赖及输入分支。新增课程数量和测试通过数不能代替复刻质量。

从仓库根复跑，输出目录必须新建：

```sh
python3 projects/duolingo-web/compile-unit12-lesson4.py --out-dir artifacts/lesson4-compiled-new
PYTHONPATH=. python3 projects/duolingo-web/freeze-unit12-lesson4.py --out-dir artifacts/lesson4-contract-new
projects/duolingo-web/run-native-course.sh artifacts/lesson4-ui-new projects/duolingo-web/fixture-reference-en-zh-v14.json --seed-progress projects/duolingo-web/evidence/english-unit12-lesson4-v1/seed-progress.json --seed-preferences projects/duolingo-web/evidence/english-unit12-lesson3-v1/native-final/progress.json.preferences.json --exercise-home-journey projects/duolingo-web/evidence/english-unit12-lesson4-v1/journey.json --source-viewport 1192 705 --audio-recorder artifacts/capture-owned-audio
```

先按`capture-owned-audio.swift`编译录音器；资源清单及导入回执保存在本目录。编译产物需和bundle一致，构建先于观察，二进制摘要记录在实际观察回执。完整Goal仍active。
