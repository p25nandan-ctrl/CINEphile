#!/bin/sh
# restarts the mock backend (empty), then runs the community journey test (needs: node build.mjs with local env, node dev/serve.mjs)
pkill -f dev/mock-gotrue.mjs 2>/dev/null; sleep 0.5
nohup node dev/mock-gotrue.mjs >/tmp/mock.log 2>&1 &
sleep 1; python3 -u dev/community_test.py
