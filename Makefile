PACKAGE=flaskel
REQ_PATH=requirements
PYVER=310

export PIP_CONFIG_FILE=pip.conf
export VERSION="$(shell grep 'current_version' .bumpversion.cfg | sed 's/^[^=]*= *//')"

define bump_version
	bumpversion -n $(1) --verbose
	@( read -p "Are you sure?!? [Y/n]: " sure && case "$$sure" in [nN]) false;; *) true;; esac )
	bumpversion $(1) --verbose
endef

define req_compile
	pip-compile $(2) \
		--resolver=backtracking \
		--no-emit-trusted-host --no-emit-index-url --build-isolation \
		-o ${REQ_PATH}/$(1).txt ${REQ_PATH}/$(1).in
endef

define check_format
	$(shell ([ "${FMT_ONLY_CHECK}" = "true" ] && echo --check || echo ""))
endef


all: clean run-tox
lint: flake pylint mypy
security: safety liccheck bandit
radon: radon-cc radon-hal radon-mi radon-raw
cqa: radon-cc-report bandit-report radon bandit
format: autoflake black isort
dev: format lint security test


compile-deps:
	$(call req_compile,requirements-build)
	$(call req_compile,requirements)
	$(call req_compile,requirements-extra)
	$(call req_compile,requirements-wsgi)
	$(call req_compile,requirements-all)
	$(call req_compile,requirements-test)
	$(call req_compile,requirements-dev)

upgrade-deps:
	$(call req_compile,requirements-build, --upgrade)
	$(call req_compile,requirements, --upgrade)
	$(call req_compile,requirements-extra, --upgrade)
	$(call req_compile,requirements-wsgi, --upgrade)
	$(call req_compile,requirements-all, --upgrade)
	$(call req_compile,requirements-test, --upgrade)
	$(call req_compile,requirements-dev, --upgrade)

install-deps:
	pip install -r ${REQ_PATH}/requirements-all.txt

clean-install-deps:
	pip install pip-tools
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
	# 51668 sqlalchemy
	# 70612 jinja2
	# 70624 flask-cors
	safety check \
		--ignore 51668 \
		--ignore 70612 \
		--ignore 70624 \
		--full-report \
		-r ${REQ_PATH}/requirements.txt \
		-r ${REQ_PATH}/requirements-extra.txt \
		-r ${REQ_PATH}/requirements-wsgi.txt

bandit:
	bandit -r --exclude ${PACKAGE}/scripts/skeleton ${PACKAGE}

bandit-report:
	bandit -f html \
		--ignore-nosec \
		--exit-zero \
		--silent \
		-r ${PACKAGE} > bandit-report.html

radon-cc:
	# cyclomatic complexity
	radon cc \
		--total-average \
		--show-complexity \
		--min C \
		--order SCORE \
		${PACKAGE}

radon-cc-report:
	# cyclomatic complexity
	radon cc \
		--md \
		--total-average \
		--show-complexity \
		--min C \
		--order SCORE \
		${PACKAGE} > radon-cc-report.md

radon-mi:
	# maintainability index
	radon mi --min B --show ${PACKAGE}

radon-hal:
	# halstead metrics
	radon hal ${PACKAGE}

radon-raw:
	# raw metrics
	radon raw -s ${PACKAGE}

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
	flake8 \
		--config=.flake8 --statistics \
		${PACKAGE} tests setup.py

pylint:
	pylint \
		-j0 --rcfile=.pylintrc --reports=y \
		${PACKAGE} tests setup.py

mypy:
	mypy \
		--ignore-missing-imports \
		--warn-unused-configs \
		--no-strict-optional \
		--show-error-codes \
		${PACKAGE} tests

run-tox:
	tox --verbose --parallel all

test:
	pytest -v -rf --strict-markers \
		--cov=${PACKAGE} --cov-report=html --cov-config .coveragerc \
		--cov-report=term-missing \
		tests

test-coverage:
	pytest -v -rf --strict-markers \
		--cov=${PACKAGE} --cov-report=xml --cov-config .coveragerc \
		--junitxml=junit-report.xml \
		--cov-report=term-missing \
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
