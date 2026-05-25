"""
PR 1: Team Agent 适配器层 — Hermes 核心 + Team 记忆管理 + 压缩钩子

设计：
- TeamMemoryManager：统一调度 4 个记忆 Provider
- TeamAgent：继承 HermesAgent，在关键钩子注入 Team 逻辑
- 记忆拼接：<memory-context> fence 防止模型混淆
- 压缩钩子：压缩前 on_pre_compress 保护关键信息
"""

from typing import List, Optional, Dict, Any
import os
import json
from pathlib import Path
from datetime import datetime


class MemoryProviderABC:
    """Memory Provider 抽象基类（对接 Hermes）"""

    def initialize(self, context: dict) -> None:
        """初始化 — 启动时调用一次"""
        pass

    def prefetch(self, session_id: str) -> str:
        """预取记忆内容 — 拼入 system prompt"""
        return ""

    def on_pre_compress(self, compaction_hint: str) -> None:
        """压缩前钩子 — 保护关键信息"""
        pass

    def sync_turn(self, action: dict, result: Any) -> None:
        """每轮同步 — 更新记忆状态"""
        pass

    def on_session_end(self) -> None:
        """会话结束 — 持久化"""
        pass


class TeamMemoryManager:
    """Team 记忆总线 — 统一调度 4 个 Provider"""

    def __init__(self, providers: List[MemoryProviderABC], session_id: str = None):
        self.providers = {p.__class__.__name__: p for p in providers}
        self.session_id = session_id or self._gen_session_id()
        self.memory_context_fence = "<memory-context>\n{}\n</memory-context>"

    @staticmethod
    def _gen_session_id() -> str:
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def initialize(self, context: dict) -> None:
        """初始化所有 Provider"""
        for name, provider in self.providers.items():
            try:
                provider.initialize(context)
            except Exception as e:
                print(f"[WARN] Provider {name} initialize failed: {e}")

    def prefetch_memory(self) -> Dict[str, str]:
        """预取所有记忆 — 返回字典便于拼接"""
        memory_blocks = {}
        for name, provider in self.providers.items():
            try:
                block = provider.prefetch(self.session_id)
                if block:
                    memory_blocks[name] = block
            except Exception as e:
                print(f"[WARN] Provider {name} prefetch failed: {e}")
                memory_blocks[name] = f"[{name} unavailable]"
        return memory_blocks

    def build_memory_context_block(self) -> str:
        """构建带 fence 的记忆块 — 防止模型混淆"""
        blocks = self.prefetch_memory()
        if not blocks:
            return ""

        content = "\n\n".join([
            f"## {name}\n{text}"
            for name, text in blocks.items()
        ])

        # 用 fence 包装，防止身份混淆
        return self.memory_context_fence.format(content)

    def on_pre_compress(self, compaction_hint: str) -> None:
        """压缩前 — 让每个 Provider 抢救关键信息"""
        for name, provider in self.providers.items():
            try:
                provider.on_pre_compress(compaction_hint)
            except Exception as e:
                print(f"[WARN] Provider {name} on_pre_compress failed: {e}")

    def sync_turn(self, action: dict, result: Any) -> None:
        """每轮同步 — 更新所有 Provider 的状态"""
        for provider in self.providers.values():
            try:
                provider.sync_turn(action, result)
            except Exception as e:
                pass  # 同步失败不阻断主循环

    def on_session_end(self) -> None:
        """会话结束 — 持久化所有 Provider"""
        for provider in self.providers.values():
            try:
                provider.on_session_end()
            except Exception as e:
                pass


class TeamAgent:
    """
    Team Agent — Hermes Agent 的增强包装

    注意：这是一个适配器，实际的 Hermes Agent 需要从 hermes.agent 导入
    如果 Hermes 还没被 install，这里只定义接口，供后续集成
    """

    def __init__(
        self,
        agent_id: str,
        team_memory_manager: Optional[TeamMemoryManager] = None,
        compression_threshold: float = 0.75,
        **kwargs
    ):
        """
        Args:
            agent_id: 代理唯一ID
            team_memory_manager: Team 记忆管理器（可选）
            compression_threshold: 压缩触发阈值（0.75 = 75% 上下文占用）
            **kwargs: 传递给底层 Agent 的参数
        """
        self.agent_id = agent_id
        self.team_mem = team_memory_manager or TeamMemoryManager([])
        self.compression_threshold = compression_threshold
        self.context_usage = 0.0
        self.history = []
        self.session_id = self.team_mem.session_id

        # 后续与实际 Hermes Agent 集成时，解开注释
        # from hermes.agent import Agent as HermesAgent
        # self._agent = HermesAgent(**kwargs)

    def should_compact(self) -> bool:
        """判断是否需要压缩"""
        return self.context_usage >= self.compression_threshold

    def trigger_compression(self, stage: int = 5) -> None:
        """触发压缩管线"""
        # 在压缩前，让记忆 Provider 抢救关键信息
        hint = f"compression_stage_{stage}_at_{self.context_usage:.1%}_context"
        self.team_mem.on_pre_compress(hint)

        # 实际压缩逻辑由压缩管线负责（team_layer/compression/）
        print(f"[INFO] Triggering compression stage {stage} (context: {self.context_usage:.1%})")

    def append_history(self, action: dict, result: Any) -> None:
        """记录一轮交互并同步 Provider"""
        self.history.append((action, result))
        self.team_mem.sync_turn(action, result)

        # 更新 context_usage（粗估：每个条目 ~500 tokens）
        self.context_usage = min(1.0, len(self.history) * 0.05)

    def get_system_prompt_with_memory(self, base_prompt: str = "") -> str:
        """生成包含记忆的系统提示词"""
        memory_block = self.team_mem.build_memory_context_block()
        if memory_block:
            return f"{base_prompt}\n\n{memory_block}"
        return base_prompt

    def finalize(self) -> None:
        """会话结束 — 持久化所有记忆"""
        self.team_mem.on_session_end()
        print(f"[INFO] Session {self.session_id} finalized")


# 便利函数：快速创建 Team Agent
def create_team_agent(
    agent_id: str,
    memory_providers: List[MemoryProviderABC] = None,
    **kwargs
) -> TeamAgent:
    """
    工厂函数 — 快速创建 Team Agent

    Example:
        agent = create_team_agent(
            "nlp-worker-1",
            memory_providers=[SoulProvider(), UserModelProvider()],
            compression_threshold=0.75
        )
    """
    mem_mgr = TeamMemoryManager(memory_providers or [])
    return TeamAgent(agent_id, team_memory_manager=mem_mgr, **kwargs)
