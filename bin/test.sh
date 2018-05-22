#!/bin/bash

APP_HOME=`dirname "$0"`/..
CONF=${APP_HOME}/bin/conf

source ${CONF}
cd ${APP_HOME} >/dev/null

source env/bin/activate


pytest test.py

deactivate
cd - >/dev/null

