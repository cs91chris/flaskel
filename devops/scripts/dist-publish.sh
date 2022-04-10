#!/bin/bash

if [[ -n "${REPO_URL}" ]]; then
	REPO_OPTS="--repository-url ${REPO_URL}"
fi

TWINE_OPTS="--verbose --skip-existing --non-interactive"

# upload to gitlab
# shellcheck disable=SC2086
twine upload ${TWINE_OPTS} ${REPO_OPTS} dist/*

# upload to pypi
# shellcheck disable=SC2086
TWINE_USERNAME=__token__ TWINE_PASSWORD=${PYPI_TOKEN} twine upload \
	${TWINE_OPTS} dist/*
