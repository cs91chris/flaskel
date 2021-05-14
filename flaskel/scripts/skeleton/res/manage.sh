#!/usr/bin/env bash

PKG_NAME=c95api
PID_FILE=".gunicorn.pid"
SITE="lib/python3.8/site-packages"
PKG_APP="${PKG_NAME}.scripts.cli:create_app()"

HOME=/home/${PKG_NAME}
BIN="${HOME}/bin"
CONF="${HOME}/${SITE}/${PKG_NAME}/scripts/gunicorn.py"


case $1 in
"reload")
    kill -0 "$(cat ${PID_FILE})"
    ;;
"run")
    ${BIN}/gunicorn -c ${CONF} ${PKG_APP}
    ;;
*)
    echo "unknown command use one of: reload, run" >&2
    exit 1
    ;;
esac
