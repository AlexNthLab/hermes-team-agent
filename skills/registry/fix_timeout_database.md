id: fix_timeout_database
desc: "Auto-generated fix for timeout_database"
trigger: "timeout.*database"
risk: low
error_sig: "timeout_database"
generated_at: "2026-05-25T11:37:24.634966"
generator: template
contract:
  input: {"code": "str", "error": "str"}
  output: {"patched_code": "str", "applied": "bool"}

## 修复步骤
1. 定位发生超时的调用点
2. 引入 tenacity 库或等价重试机制
3. 添加 @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1))
4. 确保 timeout 参数显式设置（避免无限阻塞）

## 触发样本
- Connection timeout from alice-laptop (attempt 4)
- Connection timeout from bob-desktop (attempt 1)
- Connection timeout from bob-desktop (attempt 2)
