在 Codex 中重建 ${name}：${objective}

原版：${source}
目标实现：${target}
工作区：${workspace}
项目配置：${project}
按 ${workflow} 执行：使用 RSI 改进探索，使用 E2E 模具复刻，使用原生 Goal 推动当前 Codex 持续执行。项目配置连接案例目标与工具，本 Goal 拥有本次运行的完成判定。

方法入口检查（创建时的只读快照，每轮以 project preflight 重新检查）：
${method}
先处理方法缺口：准备驱动和可恢复状态后，实际运行 RSI collect／完整池 replay／选中策略再 collect，将发现接入共同 E2E，再按模具实现和复验。人工观察历史不等于 RSI，构建与单元测试不等于 E2E。首次准备可以探索入口和修驱动，不能长期以“尚在准备”绕过这条链。方法检查不创建第二套运行状态，也不替代本 Goal 的完成判定。

完成条件：
${completion}

每轮依据真实历史与用户体验差异选择探索或实现，按上述条件交付并完成 Goal；保留剩余未知，不能用局部测试通过替代目标完成。方法与运行边界由 workflow 维护；原论文和历史实验见 ${research}。
