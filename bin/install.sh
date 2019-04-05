#!/bin/bash

APP_HOME=`dirname "$0"`/..
CONF=${APP_HOME}/bin/conf

[[ ! -f ${CONF} ]] && cp ${CONF}.example ${CONF}

source ${CONF}
cd ${APP_HOME} >/dev/null


virtualenv -p python3 env
source env/bin/activate


if [[ $? -eq 0 ]]; then
	pip install -r requirements.txt
fi

mkdir -p log .pid

for f in $(ls config/*.yaml.example); do
    cp ${f} $(echo ${f} | sed "s/\.yaml\.example/\.yaml/g")
done

cat /dev/urandom | tr -dc "a-zA-Z0-9\ @%=+&()" | head -c 128 > .secret.key

deactivate
cd - >/dev/null
