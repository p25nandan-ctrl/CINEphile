#!/bin/sh
# restarts the mock backend (empty, email confirmation OFF), then runs the v3 test (needs: node build.mjs with local env, node dev/serve.mjs)
pkill -f dev/mock-gotrue.mjs 2>/dev/null; sleep 0.5
nohup node dev/mock-gotrue.mjs >/tmp/mock.log 2>&1 &
sleep 1; curl -s "http://localhost:54321/__autoconfirm?on=1" >/dev/null; python3 -u dev/v3_test.py
