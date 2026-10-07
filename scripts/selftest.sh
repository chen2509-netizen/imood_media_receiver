#!/usr/bin/env bash
# Automatic checks that need no browser. Browser checks 1-4 (cyber_gf/docs/frontend_v2_interface.md) are manual: docs/test_guide.md.
set -uo pipefail
R="${RECEIVER_URL:-http://127.0.0.1:8030}"
LT="${LT_URL:-http://127.0.0.1:8010}"
pass=0; failn=0
check() { if [ "$2" = 1 ]; then echo "PASS  $1"; pass=$((pass+1)); else echo "FAIL  $1"; failn=$((failn+1)); fi; }

h=$(curl -s -i -X OPTIONS "$R/offer" -H "Origin: http://localhost:8010" -H "Access-Control-Request-Method: POST")
echo "$h" | head -1 | grep -q " 204" && ok=1 || ok=0; check "OPTIONS /offer -> 204" $ok
for hd in "Access-Control-Allow-Origin: \*" "Access-Control-Allow-Methods: POST, OPTIONS" "Access-Control-Allow-Headers: Content-Type"; do
  echo "$h" | grep -qi "^$hd" && ok=1 || ok=0; check "preflight header $hd" $ok
done

b=$(curl -s -i -X POST "$R/offer" -H "Content-Type: application/json" -d '{"type":"offer"}')
echo "$b" | grep -qi "^Access-Control-Allow-Origin: \*" && ok=1 || ok=0; check "POST /offer response has CORS header" $ok
echo "$b" | tail -1 | grep -q '"code": -1' && ! echo "$b" | tail -1 | grep -q '"sdp"' && ok=1 || ok=0
check "bad offer -> {code:-1, msg} without sdp" $ok

curl -s "$LT/cyber_gf/stats" | python3 -c 'import sys,json; s=json.load(sys.stdin)["data"]["sessions"]; print("INFO  LiveTalking live sessions:", [x["sessionid"] for x in s])' \
  || echo "INFO  LiveTalking stats unavailable"
echo "== $pass passed, $failn failed"
[ "$failn" = 0 ]
