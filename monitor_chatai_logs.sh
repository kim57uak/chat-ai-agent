#!/bin/bash

echo "🔍 Chat AI Agent 로그 모니터링 스크립트"
echo "=================================="

# 1. 실시간 로그 스트림
echo "1. 실시간 로그 (Ctrl+C로 중단):"
log stream --predicate 'process == "ChatAIAgent"' --style compact &
STREAM_PID=$!

# 2. 최근 로그 확인
echo -e "\n2. 최근 5분간 로그:"
log show --predicate 'process == "ChatAIAgent"' --last 5m --style compact

# 3. MCP 관련 로그만 필터링
echo -e "\n3. MCP 관련 로그:"
log show --predicate 'process == "ChatAIAgent" AND (eventMessage CONTAINS "MCP" OR eventMessage CONTAINS "mcp" OR eventMessage CONTAINS "서버")' --last 10m --style compact

# 4. 오류 로그만
echo -e "\n4. 오류 로그:"
log show --predicate 'process == "ChatAIAgent" AND messageType == Error' --last 10m --style compact

# Ctrl+C 처리
trap "kill $STREAM_PID 2>/dev/null; exit" INT

wait $STREAM_PID