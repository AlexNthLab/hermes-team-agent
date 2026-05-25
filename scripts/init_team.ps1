# init_team.ps1 — Nth Team Agent 初始化脚本（Windows PowerShell 版）

param(
    [string]$TeamRepo = "",
    [switch]$SkipGit = $false
)

Write-Host "================================"
Write-Host "Nth Team Agent 初始化脚本"
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: 检查 git
if (-not $SkipGit) {
    Write-Host "[1/5] 检查 Git 环境..." -ForegroundColor Yellow
    git --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Git 未找到，请先安装 Git" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Git 已安装" -ForegroundColor Green
}

# Step 2: 确保在 team-layer-v1 分支
Write-Host ""
Write-Host "[2/5] 确保在 team-layer-v1 分支..." -ForegroundColor Yellow
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -ne "team-layer-v1") {
    Write-Host "当前分支: $branch，切换到 team-layer-v1..."
    git checkout team-layer-v1 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "创建 team-layer-v1 分支..."
        git checkout -b team-layer-v1
    }
}
Write-Host "✅ 在分支 team-layer-v1" -ForegroundColor Green

# Step 3: 创建 .env.team
Write-Host ""
Write-Host "[3/5] 创建 .env.team..." -ForegroundColor Yellow
$envContent = @"
# Team Layer 环境变量
AUTO_COMPACT_THRESHOLD=0.75
EVOLUTION_BUDGET=15000
EVO_REPO_PATH=.
TEAM_MODE=true
"@
$envContent | Out-File -FilePath ".env.team" -Encoding utf8
Write-Host "✅ 创建 .env.team" -ForegroundColor Green

# Step 4: 初始化目录和文件
Write-Host ""
Write-Host "[4/5] 初始化目录结构..." -ForegroundColor Yellow

$dirs = @(
    "skills/registry",
    "memory",
    "logs",
    "sidechain"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "  ✓ 创建 $dir"
    }
}

# 创建初始 TEAM-SOUL.md（如果不存在）
if (-not (Test-Path "skills/TEAM-SOUL.md")) {
    Write-Host "  ✓ 创建 skills/TEAM-SOUL.md"
    $soulContent = @"
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
"@
    $soulContent | Out-File -FilePath "skills/TEAM-SOUL.md" -Encoding utf8
}

Write-Host "✅ 目录结构初始化完成" -ForegroundColor Green

# Step 5: Git 提交
Write-Host ""
Write-Host "[5/5] 提交初始化..." -ForegroundColor Yellow
if (-not $SkipGit) {
    git add -A
    git commit -m "chore: team layer initialization (Windows)" --allow-empty 2>&1 | Out-Null
    Write-Host "✅ 已提交初始化" -ForegroundColor Green
}

# 总结
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "✅ Team Layer 初始化完成！"
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "后续步骤："
Write-Host "  1. pip install -r requirements.txt"
Write-Host "  2. pip install -r requirements-team.txt"
Write-Host "  3. python team_entrypoint.py --goal '你的任务' --agent team-agent-1"
Write-Host ""

if ($TeamRepo) {
    Write-Host "配置 GitHub 私有团队仓库："
    Write-Host "  git remote add team-origin $TeamRepo"
    Write-Host "  git push team-origin team-layer-v1"
    Write-Host ""
}

Write-Host "查看详细文档: TEAM_LAYER_README.md" -ForegroundColor Cyan
