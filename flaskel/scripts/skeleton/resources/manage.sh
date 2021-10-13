#!/usr/bin/env bash

PKG_NAME=flaskel

export PID_FILE=".${PKG_NAME}.pid"

SITE="venv/lib/python3.8/site-packages"
PKG_APP="${PKG_NAME}.scripts.cli:create_app()"

HOME=/home/${PKG_NAME}
BIN=${HOME}/venv/bin
REPO_DIR=${HOME}/repo
CONF=${HOME}/${SITE}/${PKG_NAME}/scripts/gunicorn.py

case ${1} in
"reload")
    kill -SIGHUP "$(cat ${PID_FILE})"
    ;;
"run")
    echo -e "running command: ${BIN}/gunicorn -c ${CONF} ${PKG_APP}"
    exec ${BIN}/gunicorn -c ${CONF} ${PKG_APP}
    ;;
"clean")
    find ${REPO_DIR}/${PKG_NAME} -type f -name "*.c" -delete
    ;;
"build")
    cd ${REPO_DIR} || exit 1
    python setup.py bdist_wheel --cythonize
    cd || exit
    ;;
*)
    echo "unknown command use one of: reload, run, clean, build" >&2
    exit 1
    ;;
esac
