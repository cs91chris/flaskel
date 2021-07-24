PACKAGES={skeleton}
REQ_PATH=requirements
COMPILE_OPTS=--no-emit-trusted-host --no-emit-index-url --build-isolation

all: clean lint test

compile-deps:
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements.txt ${REQ_PATH}/requirements.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-test.txt ${REQ_PATH}/requirements-test.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-dev.txt ${REQ_PATH}/requirements-dev.in

update-deps:
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements.txt ${REQ_PATH}/requirements.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-test.txt ${REQ_PATH}/requirements-test.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-dev.txt ${REQ_PATH}/requirements-dev.in

install-deps:
	pip install -r ${REQ_PATH}/requirements.txt
	pip install -r ${REQ_PATH}/requirements-test.txt
	pip install -r ${REQ_PATH}/requirements-dev.txt

clean-install-deps:
	pip-sync ${REQ_PATH}/requirements*.txt

clean:
	find . -name '__pycache__' -prune  -exec rm -rf {} \;
	find . -name '.pytest_cache' -prune -exec rm -rf {} \;
	find . -name '*.pyc' -prune -exec rm -f {} \;
	find ${PACKAGES} -name '*.c' -prune -exec rm -f {} \;

lint:
	@echo "---> running black ..."
	black -t py38 ${PACKAGES} setup.py
	@echo "---> running flake8 ..."
	flake8 --config=.flake8 ${PACKAGES} setup.py
	@echo "---> running pylint ..."
	pylint --rcfile=.pylintrc ${PACKAGES} setup.py
	@echo "---> running mypy ..."
	mypy ${PACKAGES}

test:
	pytest --cov=${PACKAGES} --cov-report=html --cov-config .coveragerc tests

bump-build:
	bumpversion build --verbose

bump-release:
	bumpversion release --verbose

bump-major:
	bumpversion major --verbose

bump-minor:
	bumpversion minor --verbose

bump-patch:
	bumpversion patch --verbose
