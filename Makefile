PACKAGE=flaskel
REQ_PATH=requirements
PYVER=39

export PIP_CONFIG_FILE=pip.conf
export VERSION="$(shell grep 'current_version' .bumpversion.cfg | sed 's/^[^=]*= *//')"

define bump_version
	bumpversion -n $(1) --verbose
	@( read -p "Are you sure?!? [Y/n]: " sure && case "$$sure" in [nN]) false;; *) true;; esac )
	bumpversion $(1) --verbose
endef

define req_compile
	pip-compile $(2) \
		--no-emit-trusted-host --no-emit-index-url --build-isolation \
		-o ${REQ_PATH}/$(1).txt ${REQ_PATH}/$(1).in
endef

define check_format
	$(shell ([ "${FMT_ONLY_CHECK}" = "true" ] && echo --check || echo ""))
endef


all: clean run-tox
lint: flake pylint mypy
security: safety liccheck
format: autoflake black isort
dev: format lint test


compile-deps:
	$(call req_compile,requirements)
	$(call req_compile,requirements-extra)
	$(call req_compile,requirements-wsgi)
	$(call req_compile,requirements-test)
	$(call req_compile,requirements-dev)
	$(call req_compile,requirements-build)

upgrade-deps:
	$(call req_compile,requirements, --upgrade)
	$(call req_compile,requirements-extra, --upgrade)
	$(call req_compile,requirements-wsgi, --upgrade)
	$(call req_compile,requirements-test, --upgrade)
	$(call req_compile,requirements-dev, --upgrade)
	$(call req_compile,requirements-build, --upgrade)

install-deps:
	pip install -r ${REQ_PATH}/requirements.txt
	pip install -r ${REQ_PATH}/requirements-extra.txt
	pip install -r ${REQ_PATH}/requirements-wsgi.txt
	pip install -r ${REQ_PATH}/requirements-dev.txt
	pip install -r ${REQ_PATH}/requirements-test.txt

clean-install-deps:
	pip-sync ${REQ_PATH}/requirements*.txt

clean:
	find . -name '*.pyc' -prune -exec rm -rf {} \;
	find . -name '__pycache__' -prune -exec rm -rf {} \;
	find . -name ".mypy_cache" -prune -exec rm -rf {} \;
	find . -name '.pytest_cache' -prune -exec rm -rf {} \;
	find ${PACKAGE} -name "*.c" -prune -exec rm -rf {} \;

liccheck:
	liccheck --level PARANOID \
		--reporting liccheck-report.txt \
		-r ${REQ_PATH}/requirements.txt \
		-r ${REQ_PATH}/requirements-extra.txt \
		-r ${REQ_PATH}/requirements-wsgi.txt

safety:
	safety check --full-report \
		-r ${REQ_PATH}/requirements.txt \
		-r ${REQ_PATH}/requirements-extra.txt \
		-r ${REQ_PATH}/requirements-wsgi.txt

autoflake:
	autoflake $(call check_format) \
		--recursive \
		--in-place \
		--remove-all-unused-imports \
		--ignore-init-module-imports \
		--remove-duplicate-keys \
		--remove-unused-variables \
		${PACKAGE} tests setup.py

black:
	black $(call check_format) \
		-t py${PYVER} --workers $(shell nproc) \
		${PACKAGE} tests setup.py

isort:
	isort $(call check_format) \
		--profile black -j $(shell nproc) --py ${PYVER} \
		--atomic \
		--overwrite-in-place \
		--combine-star \
		--combine-as \
		--dont-float-to-top \
		--honor-noqa \
		--force-alphabetical-sort-within-sections \
		--multi-line VERTICAL_HANGING_INDENT \
		${PACKAGE} tests setup.py

flake:
	flake8 --config=.flake8 --statistics ${PACKAGE} tests setup.py

pylint:
	pylint --rcfile=.pylintrc ${PACKAGE} tests setup.py

mypy:
	mypy --warn-unused-configs --no-strict-optional ${PACKAGE}

run-tox:
	tox --verbose --parallel all

test:
	pytest -v -rf --strict-markers \
		--cov=${PACKAGE} --cov-report=html --cov-config .coveragerc \
		tests

test-coverage:
	pytest -v -rf --strict-markers \
		--cov=${PACKAGE} --cov-report=xml --cov-config .coveragerc \
		--junitxml=junit-report.xml \
		tests

build-dist:
	python setup.py sdist bdist_wheel

build-cython:
	python setup.py bdist_wheel --cythonize

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
