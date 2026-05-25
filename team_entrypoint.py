"""
team_entrypoint.py — Nth Team Agent 启动入口

使用方式：
    python team_entrypoint.py --goal "重构认证模块" --agent nlp-worker-1

这个脚本：
1. 初始化 Team Layer（记忆管理、压缩管线）
2. 加载 TEAM-SOUL.md 和技能库
3. 创建 TeamAgent 并运行主循环
4. 处理会话结束和持久化
"""

import sys
import argparse
from pathlib import Path

# Windows 兼容：强制 stdout/stderr UTF-8（避免 GBK 编码错误）
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass  # Python < 3.7 不支持

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from team_layer import TeamAgent, TeamMemoryManager
from team_layer.memory_providers import (
    SoulProvider,
    UserModelProvider,
    VectorProvider,
    LedgerProvider,
)
from team_layer.compression import CompressionPipeline


def create_team_context(goal: str, agent_id: str):
    """创建团队 Agent 上下文"""
    # 初始化 4 个记忆 Provider
    providers = [
        SoulProvider("skills/TEAM-SOUL.md"),
        UserModelProvider("memory/user-model.json"),
        VectorProvider("skills/registry"),
        LedgerProvider("sidechain/ledger.jsonl"),
    ]

    # 创建记忆管理器
    mem_mgr = TeamMemoryManager(providers, session_id=f"{agent_id}_{goal.replace(' ', '_')}")

    # 初始化所有 Provider
    mem_mgr.initialize({"goal": goal, "agent_id": agent_id})

    # 创建 Team Agent
    agent = TeamAgent(
        agent_id=agent_id,
        team_memory_manager=mem_mgr,
        compression_threshold=0.75,  # 从 .env.team 读取
    )

    return agent


def run_agent_loop(agent: TeamAgent, goal: str, max_iterations: int = 10):
    """
    主循环（简化版本 — 实际应与 Hermes 的 Agent.run() 集成）

    这里演示了如何集成 Team Layer 的功能：
    1. 使用 get_system_prompt_with_memory() 拼接记忆
    2. 检查压缩条件
    3. 记录到 Ledger
    """
    print(f"\n{'='*60}")
    print(f"Team Agent: {agent.agent_id}")
    print(f"Goal: {goal}")
    print(f"Session: {agent.session_id}")
    print(f"{'='*60}\n")

    # 获取包含记忆的系统提示词
    system_prompt = agent.get_system_prompt_with_memory(
        base_prompt="You are a helpful AI assistant working in a team environment."
    )
    print("[SYSTEM PROMPT]")
    print(system_prompt[:500] + "...\n")

    # 模拟主循环（实际应调用 Hermes 的模型推理）
    for iteration in range(max_iterations):
        print(f"\n--- Iteration {iteration + 1} ---")
        print(f"Context usage: {agent.context_usage:.1%}")

        # 检查是否需要压缩
        if agent.should_compact():
            agent.trigger_compression()
            # 实际压缩由 CompressionPipeline 执行
            pipeline = CompressionPipeline(
                history=agent.history,
                effort_level="high",
            )
            msg = pipeline.auto_compress(threshold=agent.compression_threshold)
            print(msg)

        # 模拟一个操作
        action = {"type": "think", "content": f"Working on goal: {goal}"}
        result = f"Progress: iteration {iteration + 1}"

        agent.append_history(action, result)

        # 记录到账本（供 EvoLoop 使用）
        agent.team_mem.providers["LedgerProvider"].record(
            agent_id=agent.agent_id,
            action_type="think",
            result=result,
            error_sig=None,
            token_cost=100,
        )

        if iteration == max_iterations - 1:
            print(f"\n✅ Completed {max_iterations} iterations")
            break

    # 会话结束 — 持久化所有记忆
    agent.finalize()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description="Nth Team Agent")
    parser.add_argument("--goal", type=str, required=True, help="Agent 的目标任务")
    parser.add_argument("--agent", type=str, default="team-agent-1", help="Agent ID")
    parser.add_argument("--iterations", type=int, default=5, help="最大迭代次数")

    args = parser.parse_args()

    try:
        # 创建 Team Agent
        agent = create_team_context(goal=args.goal, agent_id=args.agent)

        # 运行主循环
        run_agent_loop(agent, goal=args.goal, max_iterations=args.iterations)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
