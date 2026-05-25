# Nth Team Layer — Hermes 团队协作增强

一个**零改 Hermes 原文件**的团队协作魔改方案，融合 Claude Code 的 98.4% 基础设施 + OpenClaw 的持久化 + CrewAI 的结构化编排。

## 🎯 核心设计原则

| 原则 | 说明 |
|------|------|
| **零改上游** | 所有功能在 `team_layer/` 物理隔离，Hermes 原文件 100% 不动 |
| **继承 + 适配** | `TeamAgent` 继承 Hermes Agent，通过钩子注入 Team 逻辑 |
| **分层记忆** | 4 个 Provider（灵魂、用户模型、向量、账本）统一调度 |
| **5 层压缩** | 廉价优先：Budget→Snip→Microcompact→Collapse→Auto-summary |
| **7 层安全** | Effort Control、Budget Gate、Tool Restriction、Sandbox... |
| **Git SSOT** | 多终端协同，Append-only 日志，零冲突命名 |

## 📁 目录结构

```
hermes-team-agent/（基于 Hermes fork）
├── team_layer/                  # 🆕 Team 专属（100% 新增，0% 改 Hermes）
│   ├── __init__.py
│   ├── runtime.py               # ✅ PR 1: TeamAgent 适配器层
│   ├── memory_providers/        # ✅ PR 2: 4 个记忆 Provider
│   │   ├── soul_provider.py     # TEAM-SOUL.md 懒加载
│   │   ├── user_model_provider.py
│   │   ├── vector_provider.py   # 技能库索引
│   │   └── ledger_provider.py   # Append-only 账本
│   ├── compression/             # ✅ PR 3: 5 层压缩管线
│   │   ├── __init__.py
│   │   └── pipeline.py
│   ├── evolution/               # 🔄 PR 4: EvoLoop（TODO）
│   ├── git_sync/                # 🔄 PR 5: 多终端协同（TODO）
│   └── sandbox/                 # 🔄 安全隔离（TODO）
├── skills/                      # 技能库（Git managed）
│   ├── TEAM-SOUL.md            # <200 token 灵魂摘要
│   └── registry/               # 经验技能库
├── memory/                      # 持久化记忆
│   ├── user-model.json         # 用户偏好
│   └── .gitignore              # *.db 不提交
├── logs/                        # 多终端日志（Append-only）
├── sidechain/                   # Subagent 全量记录
├── .env.team                   # Team 环境变量
├── team_entrypoint.py          # 🆕 Team Agent 启动入口
├── requirements-team.txt       # Team 额外依赖
└── TEAM_LAYER_README.md        # 本文档
```

## 🚀 快速开始

### 1. 初始化（一键）

```bash
cd hermes-team-agent
bash scripts/init_team.sh
```

这会：
- ✅ 创建 team-layer-v1 分支
- ✅ 创建目录结构
- ✅ 初始化 TEAM-SOUL.md（灵魂摘要）
- ✅ 提交初始化提交

### 2. 安装依赖

```bash
pip install -r requirements.txt  # Hermes 原依赖
pip install -r requirements-team.txt  # Team 额外依赖
```

### 3. 运行 Team Agent

```bash
python team_entrypoint.py --goal "重构认证模块" --agent nlp-worker-1 --iterations 5
```

输出示例：
```
============================================================
Team Agent: nlp-worker-1
Goal: 重构认证模块
Session: nlp-worker-1_重构认证模块
============================================================

[SYSTEM PROMPT]
You are a helpful AI assistant working in a team environment.

<memory-context>
## TEAM SOUL
# TEAM SOUL (Core Summary)

## Absolute Anti-Patterns
1. **Bare API calls** — 禁止直接调用外部 API...
...

--- Iteration 1 ---
Context usage: 5.0%
Progress: iteration 1

...

✅ Completed 5 iterations
[INFO] Session nlp-worker-1_重构认证模块 finalized
```

## 🧠 4 个记忆 Provider

### SoulProvider（灵魂）
- **来源**: `skills/TEAM-SOUL.md`
- **加载**: 懒加载，仅 <200 token 核心内容
- **作用**: 注入系统提示词，确保灵魂规则永不被遗忘
- **压缩保护**: `on_pre_compress()` 确保关键词不被摘掉

```python
# 使用示例
soul = SoulProvider("skills/TEAM-SOUL.md")
soul.initialize({})
print(soul.prefetch("session_1"))  # 输出灵魂核心
```

### UserModelProvider（用户模型）
- **来源**: `memory/user-model.json`（自动生成）
- **学习**: 记录用户决策（接受/拒绝），用 Bayesian 方式更新权重
- **作用**: 个性化 Agent 行为，适应团队偏好
- **持久化**: 会话结束自动保存

```python
# 使用示例
user = UserModelProvider()
user.record_decision({"type": "code_review"}, accepted=True, reason="Good practice")
user.on_session_end()  # 保存到 user-model.json
```

### VectorProvider（向量库）
- **来源**: `skills/registry/*.md`（技能库索引）
- **能力**: 按需检索相关技能（关键字匹配，后续升级为向量搜索）
- **作用**: RAG 长尾规则，动态注入上下文
- **优势**: 不落盘向量库，由 Git 管理技能版本

```python
# 使用示例
vector = VectorProvider("skills/registry")
vector.initialize({})
results = vector.retrieve("数据库超时", top_k=3)  # 返回相关技能
```

### LedgerProvider（账本）
- **来源**: `sidechain/ledger.jsonl`（Append-only）
- **记录**: 每个操作 (timestamp, agent_id, error_sig, token_cost)
- **作用**: EvoLoop 的溯源数据，ROI 计算
- **查询**: `count_error_occurrences()`, `sum_token_cost_by_sig()`

```python
# 使用示例
ledger = LedgerProvider()
ledger.record(
    agent_id="nlp-worker-1",
    action_type="think",
    result="Completed task",
    error_sig="timeout_database",
    token_cost=150,
)
count = ledger.count_error_occurrences("timeout_database")  # 查询错误次数
```

## 🔧 5 层压缩管线

触发流程（自动判断）：

```
上下文占用率
    ↓
  50% → Budget Reduction ($0)
    ↓ 降低 effort_level（下一轮输出更短）
  60% → Snip History ($0)
    ↓ 截断 >5000 char 的巨大输出
  70% → Microcompact ($0.001)
    ↓ 压缩最后 1-2 轮为单句
  75% → Context Collapse ($0.01)
    ↓ 合并过去 5 轮为摘要
  85% → Auto-compact Summary ($0.05)
    ↓ 调用 LLM 摘要 + preserved-tail（保留最近 3 轮）
```

### 使用示例

```python
from team_layer.compression import CompressionPipeline

pipeline = CompressionPipeline(
    history=agent.history,
    max_history_chars=50000,
    effort_level="high",
)

# 自动判断并执行压缩
msg = pipeline.auto_compress(threshold=0.75)
print(msg)  # [COMPRESS] Stage 2: Snipped 3 large outputs
```

## 🔄 与 Hermes 上游同步

Team Layer 设计完全不改 Hermes 原文件，所以同步非常简单：

```bash
# 定期同步上游（月度）
cd hermes-team-agent
git fetch upstream main
git rebase upstream/main team-layer-v1

# 如果冲突，只在 team_layer/* 里处理
git diff upstream/main hermes/  # 应该显示 0 改动
```

## 📋 后续扩展（已预留接口）

### PR 4: EvoLoop 自进化引擎（下一步）
- 位置: `team_layer/evolution/`
- 功能: ROI 滞后触发 + Reflector + Verifier + Evolution Gate
- 预计: 深度集成 LedgerProvider 的错误统计

### PR 5: 多终端协同（下一步）
- 位置: `team_layer/git_sync/`
- 功能: 原子级日志采集 + 热加载 + GitHub Action 汇总
- 预计: Git sidechain 的完整生命周期

### PR 6: 加密交易 Agent（可选，后期）
- 基于 TeamAgent 继承
- 集成 Web3.py（Dex Swap、Price Oracle、Risk Monitor）
- 7 层权限控制 high-risk 交易

## 🎓 设计哲学

> **Claude Code 的 1.6% 决策 + 98.4% 基础设施**

```python
# 决策层（1.6%）— 由 Hermes Agent 负责
decision = model.decide(system_prompt, goal, available_tools)

# 基础设施（98.4%）— 由 Team Layer 负责
├─ 记忆管理（4 Provider）
├─ 上下文压缩（5 层管线）
├─ 权限控制（7 层防线）
├─ 自进化（EvoLoop）
├─ 多终端同步（Git）
└─ 沙箱隔离（Docker/隔离区）
```

这样做的好处：
- ✅ 不改 Hermes，永远可与上游同步
- ✅ TeamAgent 继承 HermesAgent，无缝集成
- ✅ 功能完全由 team_layer 承载，极易维护
- ✅ 支持渐进式扩展（记忆 → 压缩 → 安全 → 进化）

## 📚 文件约定

### `.env.team`（Team 环境变量）
```bash
AUTO_COMPACT_THRESHOLD=0.75       # 压缩触发阈值
EVOLUTION_BUDGET=15000             # 进化最大 token 预算
EVO_REPO_PATH="."                  # Team 仓库路径
TEAM_MODE=true                     # 启用 Team 模式
```

### `skills/TEAM-SOUL.md`（灵魂摘要）
<200 token，包含：
- 5 个绝对反模式
- Preferred Stack
- Evolution Policy
- 动态加载指令

### `memory/user-model.json`（用户偏好）
```json
{
  "preferences": {
    "code_review": 0.8,
    "refactor": 0.5,
    "testing": 0.9
  },
  "history": [
    {"timestamp": "2026-05-25T10:00:00", "action": "code_review", ...}
  ]
}
```

### `sidechain/ledger.jsonl`（Append-only 账本）
```jsonl
{"timestamp": "2026-05-25T10:00:00", "agent_id": "nlp-1", "action_type": "think", ...}
{"timestamp": "2026-05-25T10:01:00", "agent_id": "nlp-1", "action_type": "execute", ...}
```

## 🛠️ 故障排除

### Q: 如何与团队共享升级？
A: 推送到私有 Git 仓库
```bash
git remote add team-origin <your-private-repo>
git push team-origin team-layer-v1
# 团队成员拉取 + 热加载
```

### Q: 如何禁用某个 Provider？
A: 在 `team_entrypoint.py` 中注释掉
```python
providers = [
    SoulProvider(...),
    # UserModelProvider(...),  # 禁用
    VectorProvider(...),
    LedgerProvider(...),
]
```

### Q: 压缩后上下文会变短吗？
A: 会。但 preserved-tail 机制保留最近 3 轮高保真交互，防止遗忘关键上下文。

### Q: 如何集成实际的 Hermes Agent？
A: 修改 `team_entrypoint.py` 中的 `run_agent_loop()`
```python
# 替换 mock，使用真实 Hermes
from hermes.agent import Agent as HermesAgent
hermes_agent = HermesAgent(...)
result = hermes_agent.run(goal)
```

## 📖 参考

- **Claude Code 设计**: 1.6% 决策核心 + 98.4% 阻断/压缩基础设施
- **Hermes Agent**: https://github.com/NousResearch/hermes-agent
- **Team Layer 源**: 基于"团队可进化 AGENT"设计文档（2026-03-28）

---

**Created**: 2026-05-25  
**Status**: PR 1-3 完成，PR 4-5 预留  
**Maintainer**: Nth Team Agent  
**License**: Inherits from Hermes
