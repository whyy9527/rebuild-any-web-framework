# 手动 MCP 验证工具

持续执行使用 [重建工作流](../rebuild/WORKFLOW.md)与 Codex 原生 Goal。旧 Stop Hook 及 SessionStart／UserPromptSubmit 适配已删除；本工具只管理显式验证尝试、反馈、暂停和预算，不自动续跑 Codex。其 complete 只针对选定 verifier，不代表完整复刻完成。原生 Goal 路径不需要安装或启动这套兼容状态。

确需手动 MCP 验证时，从仓库根运行：

```sh
python3 -m workflows.harness.install --repo . --workspace <目标项目>
```

安装器只注册项目 `.codex/config.toml` 中的 MCP，启动器与状态在 `.codex/exploration-lab/`。升级时备份配置并移除该目标项目由旧安装器注册的三个 Hook 和 `hook.sh`，保留其他 Hook、MCP 与用户设置。不创建 hooks.json 或启用 Hook 功能，不修改全局配置；其他曾安装的项目需分别显式运行升级。已打开的会话需重新打开才能刷新宿主注册。

手动调用协议：

1. `exploration_start`：传入工作目录、当前 session_id、目标、真实 verifier argv 和有限次数／失败／时间预算。可传 `acceptance_paths` 冻结验收输入、`verify_seconds` 限制单次验证；省略路径时冻结默认 tests、Tests、e2e 及常见配置。
2. `exploration_next`：读取反馈、记录假设并预留尝试；Codex 使用原生工具修改。
3. `exploration_verify`：执行冻结的验收并返回实际结果，失败后读取反馈。不可改冻结测试绕过验收。
4. `exploration_status`：读取当前验证任务与反馈。
5. `exploration_pause` / `exploration_resume`：由当前 Codex 响应用户暂停／恢复要求并显式调用，不重置预算。
6. `exploration_adopt`：用户明确选择同工作区的暂停任务后转交 session_id，保留反馈和预算，不自动恢复。正在验收、跨工作区或目标已有未完成任务均拒绝。

工具不替代权限审批、真人验收或美学评价。历史 Hook 消融与宿主证据保留在案例中；复跑使用记录的 Git 版本，不把退役适配重新引入当前运行链。

`python3 -m workflows.harness.diagnose --workspace <项目> --out artifacts/host.json` 可检查 MCP 清单及遗留 Hook；`python3 -m unittest discover -v` 验证实现。
