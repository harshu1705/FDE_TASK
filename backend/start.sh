#!/usr/bin/env bash
uvicorn_cmd="python -m uvicorn"
$uvicorn_cmd main:app --host 0.0.0.0 --port $PORT