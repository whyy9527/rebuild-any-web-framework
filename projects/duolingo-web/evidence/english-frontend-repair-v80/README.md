# 共享前端模具修复与原版继续探索

本批消费第四课真实整图失败，优先修共享题面、反馈及档案提示，没有继续扩题数。原版参考为上一批已冻结的1192×705记录；`baseline.json`指向60dc6bc及原始失败。1:1尚未完成，Goal保持active。

## 实际修复

原来的题面按intrinsic内容撑开，把底栏挤到705点内容窗之外。现在为普通题面保留实测header82／footer140的布局空间，翻译题显式组合指示条、标题、角色、答题行与词库；原版新单词SVG直接从已冻结DOM提取、隔离浏览器3x渲染。角色Rive配置原字段yOffsetPercentage为正，但原版实际CSS为负百分比translate；修正Swift纵向符号，保留实际原版文件／状态机，不用静态替代图冒充动画。

正确反馈接原版勾图和实测底栏；档案页接已保存的原版Duo持手机图、300×50按钮及实际几何。原生原档案次要项曾是不可点击Text，现在有实际按钮与注册路由；该页建档后续流程仍待同源验证。

首轮及修正轮各完整执行48状态，0驱动失败。最终交付再次先构建后观察，回执记录实际二进制SHA；源题面、反馈、结算、档案与主页图像全部保留。38业务核心检查通过，前端比较器12测试通过；`swift test`报告没有test target，本项目业务检查入口为LearningCoreChecks，不能把该命令记成测试通过。

## 模具仍然失败

v80逐项保留v79的26779要求，另从原始记录补8项非交互标题字形／变换后Canvas／CSS背景图几何。它们是诊断遗漏的补齐，不是事前注册的RSI收益指标。严格比较不放宽几何、不对齐搜索、不遮图；当前档案两按钮和原图几何一致，翻译词块横向位置及宽度已接近原版，但仍有实际半点取整、题面、气泡／提示词、进度栏、可跳过按钮等差异。整图继续fail。

`baseline-v80.json`和`delivery-comparison/frontend.json`同契约比较，最终925pass／720fail／24058not_run／1084unavailable；先前修正轮`frontend-v80.json`保留；`status-changes.json`保留变化，`image-diagnostics.json`保存逐图RGB差异，不能以局部改善宣称完成。新版本只有一条课程轨迹实际跑过，其它继承要求not_run，不是全仓回归。

真实自有应用录音同时包含回放／提交动作，麦克风关闭。原语音拟合相关性约0.99975、增益约0.99957；正确音效相关性0.999858、增益0.349951。仅证明原资源出现在应用实际输出，不是源浏览器声学／延迟／全混音一致。

## 反馈如何改变下一步

`exploration-policy.json`在执行前明确优先尝试前部分故事入口，避免为了电台锁定一直刷下一课。实际外层role按钮点击只滚到前部分，随后再次点击外层及真正内层button仍未捕获故事入口。`source/`保留前后状态、具体命中DOM和实际回执；不能据此虚构故事内容或判定解锁条件。探索继续保留unknown。

`mold-gaps.json`、`exploration-feedback.json`与历史/frontier把非交互几何漏验、错误CSS偏移和未进入故事的反例传给后续选择。下一批优先真实跳过结果、提示词hover／focus及原版气泡、挑战指示条／缺失角色和故事前置条件，同时修主页及声音差异。原始Dream-RSI、Cordis和真实04负结果、05／06部署保留于[研究说明](../../../../docs/RESEARCH.md)。本批是主代理反馈闭环，未新增独立模型策略实验，不宣称RSI因果收益；匹配预算产品质量消融仍待完成。

## 复跑

从仓库根运行，OUT用新目录。先按上一批[命令](../english-unit12-lesson4-v1/README.md)实际执行课程，再比较：

```sh
python3 projects/duolingo-web/freeze-frontend-repair.py --out-dir artifacts/repair80-contract-new
python3 projects/duolingo-web/compare-frontend-repair.py --observed OUT/observed.json --out-dir artifacts/repair80-compare-new
swift run --package-path projects/education-swift LearningCoreChecks
python3 -m unittest tests.rebuild.test_frontend -q
```

前端比较当前预期退出1并产出fail回执，不能吞掉退出码当通过。`comparison.html`仅展示原图／实测Swift并排，不替代可执行验收。
