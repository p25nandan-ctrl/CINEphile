#!/bin/sh
# restarts the mock backend so each run starts empty, then runs the journey test
pkill -f dev/mock-gotrue.mjs 2>/dev/null; sleep 0.5
nohup node dev/mock-gotrue.mjs >/tmp/mock.log 2>&1 &
sleep 1; python3 -u dev/learn_test.py
