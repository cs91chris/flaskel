FROM python:3.8 AS builder

WORKDIR /tmp

COPY ./{skeleton} ./{skeleton}
COPY ./setup.py ./setup.py
COPY ./requirements ./requirements
COPY ./devops/build.sh .

RUN bash ./build.sh


FROM python:3.8-slim as base-app

ENV APP_USER flaskel

RUN groupadd -g 1000 ${APP_USER} \
    && useradd -m -d /app -s /bin/bash -g ${APP_USER} -u 1000 ${APP_USER}

USER ${APP_USER}

WORKDIR /app

COPY --chown=${APP_USER}:${APP_USER} --from=builder /tmp/dist ./dist
COPY --chown=${APP_USER}:${APP_USER} ./devops/base/ ./

RUN python -m venv venv \
    && venv/bin/pip install wheel dist/* \
    && rm -rf .cache/pip dist

ENV PATH /app/venv/bin:${PATH}

ENTRYPOINT ["bash", "/app/scripts/entrypoint"]
CMD ["bash"]
