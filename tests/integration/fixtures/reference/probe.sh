#!/usr/bin/env bash
# Fake MCP server for integration tests: dump the environment we were launched
# with, then linger so the harness sees a running server.
env > /tmp/aps_probe_env.txt
sleep 5
