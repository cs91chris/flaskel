FROM python:3.8 AS builder
WORKDIR /tmp

COPY . /tmp

RUN pip install -r requirements/requirements-build.txt ; \
    python setup.py bdist_wheel --cythonize

FROM python:3.8-slim
WORKDIR /app

COPY --from=builder /tmp/dist ./dist
COPY --from=builder /tmp/res ./res

RUN pip install gunicorn dist/*

ENV CONF_PATH=/app/res
ENV APP_HOST=0.0.0.0

EXPOSE 5000

CMD [ \
    "gunicorn", \
    "-c", "/usr/local/lib/python3.8/site-packages/{skeleton}/scripts/gunicorn.py", \
    "{skeleton}.scripts.cli:create_app()" \
]
