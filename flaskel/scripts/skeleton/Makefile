PACKAGE={skeleton}
COMPOSE_PATH=devops
REQ_PATH=requirements
IMAGES_PATH=dist/images
SERVICE_PATH=devops/services
COMPILE_OPTS=--no-emit-trusted-host --no-emit-index-url --build-isolation

define docker_save
	docker save $(1) | gzip -c > ${IMAGES_PATH}/$(1).tar.gz
endef

define docker_publish
	docker tag $(1) ${TTP_REGISTRY}$(1):${TTP_VERSION}
	docker push ${TTP_REGISTRY}$(1):${TTP_VERSION}
endef

define bump_version
	bumpversion -n $(1) --verbose
	@( read -p "Are you sure?!? [Y/n]: " sure && case "$$sure" in [nN]) false;; *) true;; esac )
	bumpversion $(1) --verbose
endef

define copy_requirements
	cp ${REQ_PATH}/requirements.txt ${SERVICE_PATH}/${PACKAGE}/requirements.txt
endef

define req_compile
	pip-compile $(2) ${COMPILE_OPTS} -o ${REQ_PATH}/$(1).txt ${REQ_PATH}/$(1).in
endef


all: clean lint clean-install-deps test

compile-deps:
	$(call req_compile,requirements)
	$(call req_compile,requirements-test)
	$(call req_compile,requirements-dev)
	$(call copy_requirements)

upgrade-deps:
	$(call req_compile,requirements, --upgrade)
	$(call req_compile,requirements-test, --upgrade)
	$(call req_compile,requirements-dev, --upgrade)
	$(call copy_requirements)

install-deps:
	pip install -r ${REQ_PATH}/requirements.txt
	pip install -r ${REQ_PATH}/requirements-test.txt
	pip install -r ${REQ_PATH}/requirements-dev.txt

clean-install-deps:
	pip-sync ${REQ_PATH}/requirements*.txt

clean:
	find . -name '*.pyc' -prune -exec rm -rf {} \;
	find . -name '__pycache__' -prune -exec rm -rf {} \;
	find . -name '.pytest_cache' -prune -exec rm -rf {} \;
	find ${PACKAGE} -name "*.c" -prune -exec rm -rf {} \;
	find ${PACKAGE} -name ".mypy_cache" -prune -exec rm -rf {} \;

lint:
	black -t py38 ${PACKAGE} tests setup.py
	flake8 --config=.flake8 ${PACKAGE} tests setup.py
	pylint --rcfile=.pylintrc ${PACKAGE} tests setup.py
	mypy --install-types --non-interactive --no-strict-optional ${PACKAGE} tests

test:
	pytest --cov=${PACKAGE} --cov-report=html --cov-config .coveragerc tests

build-images:
	mkdir -p ${IMAGES_PATH}
	docker-compose -p ${PACKAGE} -f ${COMPOSE_PATH}/docker-compose.yaml build
	$(call docker_save,${PACKAGE})

publish-images:
	$(call docker_publish,${PACKAGE})

start-all-services:
	docker-compose -p ${PACKAGE} -f ${COMPOSE_PATH}/docker-compose.yaml up

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
