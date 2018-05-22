#!/bin/bash

APP_HOME=`dirname "$0"`/..
CONF=${APP_HOME}/bin/conf

source ${CONF}
cd ${APP_HOME} >/dev/null

source env/bin/activate


if [[ -z "${FLASK_ENV}" || "${FLASK_ENV}" == "development" ]]
then
	python app.py
else
	if [[ -z ${APP_HOST}  || -z ${APP_PORT} ]]
	then
		echo -e "\nERROR: you must set APP_HOST and APP_PORT variables\n"
		exit 1
	fi

    export UWSGI_MODULE=${FLASK_APP}
    export UWSGI_HTTP=${APP_HOST}:${APP_PORT}

	# choose between uwsgi or gunicorn
	# default is uwsgi because it seems to be faster than gunicorn
    #
    uwsgi --yaml ${APP_HOME}/config/uwsgi.yaml

    # gunicorn -c ${APP_HOME}/gunicorn.py ${FLASK_APP}
fi

deactivate

