export PIP_CONFIG_FILE=pip.conf

PACKAGE=flaskel
REQ_PATH=requirements
COMPILE_OPTS=--no-emit-trusted-host --no-emit-index-url --build-isolation
CONFIRM=@( read -p "Are you sure?!? [Y/n]: " sure && case "$$sure" in [nN]) false;; *) true;; esac )

all: clean lint clean-install-deps test

compile-deps:
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements.txt ${REQ_PATH}/requirements.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-extra.txt ${REQ_PATH}/requirements-extra.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-test.txt ${REQ_PATH}/requirements-test.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-dev.txt ${REQ_PATH}/requirements-dev.in

upgrade-deps:
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements.txt ${REQ_PATH}/requirements.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-extra.txt ${REQ_PATH}/requirements-extra.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-test.txt ${REQ_PATH}/requirements-test.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-dev.txt ${REQ_PATH}/requirements-dev.in

install-deps:
	pip install -r ${REQ_PATH}/requirements.txt
	pip install -r ${REQ_PATH}/requirements-extra.txt
	pip install -r ${REQ_PATH}/requirements-dev.txt
	pip install -r ${REQ_PATH}/requirements-test.txt

clean-install-deps:
	pip-sync ${REQ_PATH}/requirements*.txt

clean:
	find . -name '__pycache__' -prune -exec rm -rf {} \;
	find . -name '.pytest_cache' -prune -exec rm -rf {} \;
	find . -name '*.pyc' -prune -exec rm -f {} \;

lint:
	@echo "---> running black ..."
	black -t py38 ${PACKAGE} tests setup.py
	@echo "---> running flake8 ..."
	flake8 --config=.flake8 ${PACKAGE} tests setup.py
	@echo "---> running pylint ..."
	pylint --rcfile=.pylintrc ${PACKAGE} tests setup.py
	@echo "---> running mypy ..."
	mypy --install-types --non-interactive --no-strict-optional ${PACKAGE}

test:
	pytest --cov=${PACKAGE} --cov-report=html --cov-config .coveragerc tests

build-dist:
	python setup.py sdist bdist_wheel

bump-build:
	bumpversion -n build --verbose
	${CONFIRM}
	bumpversion build --verbose

bump-beta:
	bumpversion -n prerelease --verbose
	${CONFIRM}
	bumpversion prerelease --verbose

bump-major:
	bumpversion -n major --verbose
	${CONFIRM}
	bumpversion major --verbose

bump-minor:
	bumpversion -n minor --verbose
	${CONFIRM}
	bumpversion minor --verbose

bump-patch:
	bumpversion -n patch --verbose
	${CONFIRM}
	bumpversion patch --verbose
