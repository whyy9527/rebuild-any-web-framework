# Dream-RSI 协议检查

这是算法／运行接线夹具：发现命令从已恢复快照修改一个 `total()` 程序，独立评价器实际运行四个用例。自动 reviser 根据真实回放中深层节点的结果生成策略修订。它是确定性程序，不是 LLM，也不是 App 复刻效果实验。

```sh
python3 -m workflows.rebuild.project run --workspace . --project projects/dream-rsi-check/rebuild.json --command rsi_cycle --out artifacts/dream-check
python3 -m workflows.rebuild.dream inspect --workspace . --pool artifacts/dream-check/iteration-2/pool.json
python3 -m unittest tests.rebuild.test_dream -v
```

结果留在新的本地 artifacts 目录。查看每轮 `online/tree.json`、`dream/evaluation.json` 与 `pool.json`，可核对父子快照、实际评价、所有历史世界评分和下一轮部署的策略 SHA。

当前 Codex 可以绕过夹具 reviser，按 [RSI 接口](../../workflows/rebuild/RSI.md)用 `collect/replay` 读取反馈、直接写候选策略、评价并部署。此模式不启动嵌套模型。实际验证与限制见 [验证记录](VERIFICATION.md)。
