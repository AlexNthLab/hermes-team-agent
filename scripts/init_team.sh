#!/bin/bash
# init_team.sh — Team Layer 一键初始化

set -e

echo "================================"
echo "Nth Team Agent 初始化脚本"
echo "================================"

# Step 1: 检查当前分支
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "[1/6] Current branch: $BRANCH"

if [ "$BRANCH" != "team-layer-v1" ]; then
    echo "⚠️  Expected branch 'team-layer-v1', got '$BRANCH'"
    echo "Switching to team-layer-v1..."
    git checkout team-layer-v1 || echo "Creating team-layer-v1..."
    git checkout -b team-layer-v1
fi

# Step 2: 确保目录结构
echo "[2/6] Creating directory structure..."
mkdir -p team_layer/memory_providers
mkdir -p team_layer/compression
mkdir -p team_layer/evolution
mkdir -p team_layer/git_sync
mkdir -p team_layer/sandbox
mkdir -p skills/registry
mkdir -p logs
mkdir -p sidechain
mkdir -p memory

# Step 3: 创建初始化文件
echo "[3/6] Creating initialization files..."

# .env.team 配置
cat > .env.team <<'EOF'
# Team Layer 环境变量
AUTO_COMPACT_THRESHOLD=0.75
EVOLUTION_BUDGET=15000
EVO_REPO_PATH="."
TEAM_MODE=true
EOF

# .gitignore 更新（保证关键文件不提交）
cat >> .gitignore <<'EOF'
# Team Layer 本地文件（不提交 Git）
memory/*.db
memory/*.jsonl
memory/*-cache/
skills/vector_index.db
logs/*.jsonl
.env.local
.env.team
.DS_Store
EOF

# Step 4: 创建初始 TEAM-SOUL.md
echo "[4/6] Creating TEAM-SOUL.md..."
cat > skills/TEAM-SOUL.md <<'EOF'
# TEAM SOUL (Core Summary)

## Absolute Anti-Patterns
1. **Bare API calls** — 禁止直接调用外部 API，必须加 timeout + retry
2. **Cross-agent memory pollution** — 子代理结果必须通过 sidechain 隔离
3. **Mutable shared state** — 所有状态通过 Git append-only 日志
4. **Context explosion** — 压缩阈值 75%，必须分层执行
5. **Unaudited tool execution** — 所有工具调用必须通过 permission_gate

## Preferred Stack
- **Memory**: CLAUDE.md 式可编辑 + 向量索引 + append-only 账本
- **Compression**: 5 层管线（廉价优先）
- **Safety**: 7 层权限模型 + ML classifier + 沙箱隔离
- **Sync**: Git SSOT + 原子级热加载 + 零冲突日志命名

## Evolution Policy
- 触发条件：同类错误 ≥3 次 AND 浪费 token > 进化预算的 1.5 倍
- 流程：Reflector Subagent → Verifier → Evolution Gate
- 低风险自动 Merge，高风险等待人工审批
EOF

# Step 5: 创建示例技能
echo "[5/6] Creating example skill..."
cat > skills/registry/example_skill.md <<'EOF'
id: example_skill
desc: "示例技能 — 演示 Skill Registry 的结构"
trigger: "example"
risk: low
contract:
  input: {"query": "str"}
  output: {"result": "str"}

## 修复步骤
1. 这是一个示例技能
2. 在 skills/registry/ 中添加更多 .md 文件
3. 支持自动热加载
EOF

# Step 6: Git 提交
echo "[6/6] Committing initialization..."
git add .env.team .gitignore skills/ team_layer/ scripts/ 2>/dev/null || true
git commit -m "chore: initialize team layer structure (no upstream changes)" --allow-empty

echo ""
echo "✅ Team Layer 初始化完成！"
echo ""
echo "后续步骤："
echo "1. pip install -r requirements.txt"
echo "2. python team_entrypoint.py --goal 'Your task here'"
echo ""
echo "配置 GitHub 私有团队仓库："
echo "  git remote add team-origin <your-private-repo>"
echo "  git push team-origin team-layer-v1"
echo ""
