#!/bin/bash

APP_HOME=$(dirname "$0")/..
CONF=${APP_HOME}/bin/conf
[[ ! -f ${CONF} ]] && cp ${CONF}.example ${CONF}


source ${CONF}
cd ${APP_HOME} > /dev/null

source env/bin/activate


if [[ -z "${FLASK_ENV}" || "${FLASK_ENV}" == "development" ]]
then
	python app.py
else
	if [[ -z "${APP_HOST}" || -z "${APP_PORT}" ]]
	then
		echo -e "\nERROR: you must set APP_HOST and APP_PORT variables\n"
		exit 1
	fi

    gunicorn -c ${APP_HOME}/gunicorn.py ${FLASK_APP}
fi

deactivate

