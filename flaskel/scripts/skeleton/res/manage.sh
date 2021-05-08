#!/usr/bin/env bash

BASE=res
PKG=flaskel

case $1 in
"reload")
    kill -0 "$(cat .gunicorn.pid)"
    ;;
"run")
    gunicorn -c "${BASE}/gunicorn.py" "${PKG}.scripts.cli:create_app()"
    ;;
*)
    echo "unknown command use one of: reload, run"
    exit 1
    ;;
esac
