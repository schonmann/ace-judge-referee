FROM python:2.7.15-slim as builder

FROM builder as development

LABEL maintainer="Antonio Schönmann <antonio.schonmann@gmail.com>"

WORKDIR /app

RUN mkdir emafiles

COPY requirements.txt requirements.txt

ENV BUILD_DEPS="cmake pkg-config libx11-dev libatlas-base-dev libgtk-3-dev libboost-python-dev unixodbc-dev libsqlite3-dev" \
    APP_DEPS="curl libpq-dev build-essential procps"

RUN pip install --upgrade pip

RUN apt-get update \
  && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} --no-install-recommends \
  && pip install -r requirements.txt \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /usr/share/doc && rm -rf /usr/share/man \
  && apt-get purge -y --auto-remove ${BUILD_DEPS} \
  && apt-get clean

COPY . .

CMD ["celery", "-A", "main", "worker", "--loglevel=info"]