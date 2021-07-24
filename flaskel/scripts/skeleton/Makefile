PACKAGES={skeleton}
REQ_PATH=requirements
REQ=requirements
REQUIREMENTS=${REQ}.in ${REQ}-test.in ${REQ}-dev.in
COMPILE_OPTS=--no-emit-trusted-host --no-emit-index-url --build-isolation

all: clean lint clean-install-deps test

compile-deps:
	for req in $(REQUIREMENTS); do \
        out_req=$$(echo $${req} | sed 's/.in/.txt/') ; \
        pip-compile ${COMPILE_OPTS} -o ${REQ_PATH}/$${out_req} ${REQ_PATH}/$${req} ; \
    done

upgrade-deps:
	for req in $(REQUIREMENTS); do \
        out_req=$$(echo $${req} | sed 's/.in/.txt/') ; \
        pip-compile --upgrade ${COMPILE_OPTS} -o ${REQ_PATH}/$${out_req} ${REQ_PATH}/$${req} ; \
    done

install-deps:
	pip install -r ${REQ_PATH}/requirements*.txt

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
	mypy --install-types --non-interactive ${PACKAGES}

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
