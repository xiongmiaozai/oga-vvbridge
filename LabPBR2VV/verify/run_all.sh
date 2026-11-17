#!/usr/bin/env bash
# run_all.sh — 一键复跑 PBR2VV 全套验证（纯网页版形态，无需 Android SDK）
# 用法：bash verify/run_all.sh
# 官方包路径可用环境变量 OFFICIAL_ZIP 覆盖。
# 2026-11-15：APK 工程已移除，去掉原「同步网页版 → APK assets」步骤。
# 2026-11-15：新增第 6 步 clean_pack 自测（叠加修复回归）。
set -euo pipefail

BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"
mkdir -p verify/out
PORT="${CDP_PORT:-9222}"

echo "======== 1/6 工程静态一致性 ====="
python3.11 verify/static_check.py

echo "======== 2/6 准备 Chromium (CDP :$PORT) ======="
STARTED=0
if ! curl -fsS "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1; then
  rm -rf /tmp/chrome-pbr2vv && mkdir -p /tmp/chrome-pbr2vv
  chromium --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --remote-debugging-port="$PORT" --user-data-dir=/tmp/chrome-pbr2vv \
    --disable-background-networking --no-first-run \
    "file://$BASE/LabPBR2VV.html" > /tmp/chrome-pbr2vv/chrome.log 2>&1 &
  CHROME_PID=$!
  STARTED=1
  trap 'kill "$CHROME_PID" 2>/dev/null || true' EXIT
  for _ in $(seq 1 60); do
    curl -fsS "http://127.0.0.1:$PORT/json/version" >/dev/null 2>&1 && break
    sleep 0.25
  done
fi
echo "  CDP 就绪 (自启动=$STARTED)"

echo "======== 3/6 真实浏览器端到端转换 ======="
CDP_PORT="$PORT" node verify/cdp_run.mjs

echo "======== 4/6 逐文件校验 .mcpack ======="
python3.11 verify/verify_pack.py

echo "======== 5/6 官方样例包 MERS 回归 ======="
OFFICIAL="${OFFICIAL_ZIP:-/root/.codebuddy/artifact/2f8a7d30-9c21-4f0b-1d72-5249b0df3000/official.zip}"
if [ -f "$OFFICIAL" ]; then
  OFFICIAL_ZIP="$OFFICIAL" python3.11 verify/official_regression.py
else
  echo "  跳过：未找到官方样例包 ($OFFICIAL)"
  echo "  如需复跑本步，先设置 OFFICIAL_ZIP=/path/to/bedrock-samples-*-full.zip"
fi

echo "======== 6/6 清洗工具自测（叠加修复回归） ======="
python3.11 verify/clean_pack.py --selftest 2>/dev/null | tail -n 12

echo ""
echo "全部完成。产物："
echo "  $BASE/示例_LabPBR2VV.mcpack"
echo "  $BASE/verify/out/{static_check,cdp_result,report,pack_check,official_regression}.json"
