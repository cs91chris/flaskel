PACKAGES=flaskel
REQ_PATH=requirements
COMPILE_OPTS=--no-emit-trusted-host --no-emit-index-url --build-isolation

compile-deps:
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements.txt ${REQ_PATH}/requirements.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-test.txt ${REQ_PATH}/requirements-test.in
	pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-dev.txt ${REQ_PATH}/requirements-dev.in

update-deps:
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements.txt ${REQ_PATH}/requirements.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-test.txt ${REQ_PATH}/requirements-test.in
	pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/requirements-dev.txt ${REQ_PATH}/requirements-dev.in

install-deps:
	pip install -r ${REQ_PATH}/requirements-dev.txt
	pip install -r ${REQ_PATH}/requirements-test.txt
	pip install -r ${REQ_PATH}/requirements.txt

clean-install-deps:
	pip-sync ${REQ_PATH}/requirements*.txt

clean:
	find . -name '__pycache__' -prune  -exec rm -rf {} \;
	find . -name '.pytest_cache' -prune -exec rm -rf {} \;
	find . -name '*.pyc' -prune -exec rm -f {} \;

lint:
	@echo "-> running black..."
	black -t py38 ${PACKAGES} ./setup.py
	@echo "-> running flake8..."
	flake8 --config=.flake8 ${PACKAGES} ./setup.py
	@echo "-> running pylint..."
	pylint --rcfile=.pylintrc ${PACKAGES} ./setup.py

test:
	pytest --cov=${PACKAGES} --cov-report=html --cov-config .coveragerc tests
	date

all: clean lint test

version-build:
	bumpversion build --verbose

version-release:
	bumpversion release --verbose

version-major:
	bumpversion major --verbose

version-minor:
	bumpversion minor --verbose

version-patch:
	bumpversion patch --verbose
