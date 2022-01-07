export PIP_CONFIG_FILE=pip.conf

PACKAGE=flaskel
REQ_PATH=requirements
COMPILE_OPTS=--no-emit-trusted-host --no-emit-index-url --build-isolation

define bump_version
	bumpversion -n $(1) --verbose
	@( read -p "Are you sure?!? [Y/n]: " sure && case "$$sure" in [nN]) false;; *) true;; esac )
	bumpversion $(1) --verbose
endef

define req_compile
	pip-compile $(2) ${COMPILE_OPTS} -o ${REQ_PATH}/$(1).txt ${REQ_PATH}/$(1).in
endef


all: clean lint test security

compile-deps:
	$(call req_compile,requirements)
	$(call req_compile,requirements-extra)
	$(call req_compile,requirements-test)
	$(call req_compile,requirements-dev)

upgrade-deps:
	$(call req_compile,requirements, --upgrade)
	$(call req_compile,requirements-extra, --upgrade)
	$(call req_compile,requirements-test, --upgrade)
	$(call req_compile,requirements-dev, --upgrade)

install-deps:
	pip install -r ${REQ_PATH}/requirements.txt
	pip install -r ${REQ_PATH}/requirements-extra.txt
	pip install -r ${REQ_PATH}/requirements-dev.txt
	pip install -r ${REQ_PATH}/requirements-test.txt

clean-install-deps:
	pip-sync ${REQ_PATH}/requirements*.txt

clean:
	find . -name '*.pyc' -prune -exec rm -rf {} \;
	find . -name '__pycache__' -prune -exec rm -rf {} \;
	find . -name '.pytest_cache' -prune -exec rm -rf {} \;
	find ${PACKAGE} -name "*.c" -prune -exec rm -rf {} \;
	find ${PACKAGE} -name ".mypy_cache" -prune -exec rm -rf {} \;

security:
	liccheck \
		-r ${REQ_PATH}/requirements.txt \
		-r ${REQ_PATH}/requirements-extra.txt

	# ignore flask-caching
	safety check --full-report \
		--ignore 40459 \
		-r ${REQ_PATH}/requirements.txt \
		-r ${REQ_PATH}/requirements-extra.txt

lint:
	black -t py38 ${PACKAGE} tests setup.py
	flake8 --config=.flake8 ${PACKAGE} tests setup.py
	pylint --rcfile=.pylintrc ${PACKAGE} tests setup.py
	mypy --install-types --non-interactive --no-strict-optional ${PACKAGE}

test:
	pytest --cov=${PACKAGE} --cov-report=html --cov-config .coveragerc tests

build-dist:
	python setup.py sdist bdist_wheel

bump-build:
	$(call bump_version,build)

bump-release:
	$(call bump_version,release)

bump-major:
	$(call bump_version,major)

bump-minor:
	$(call bump_version,minor)

bump-patch:
	$(call bump_version,patch)
