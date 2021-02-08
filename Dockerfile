FROM python:2.7.15-slim as builder

FROM builder as development

LABEL maintainer="Antonio Schönmann <antonio.schonmann@gmail.com>"

WORKDIR /app

RUN mkdir emafiles

ENV BUILD_DEPS="wget cmake pkg-config libx11-dev libatlas-base-dev libgtk-3-dev libboost-python-dev unixodbc-dev libsqlite3-dev" \
    APP_DEPS="curl gnuplot libpq-dev build-essential procps"

RUN pip install --upgrade pip

RUN apt-get update \
  && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} --no-install-recommends \
  && wget http://archive.ubuntu.com/ubuntu/pool/universe/g/gnuplot/gnuplot_4.6.6-3_all.deb \
  && dpkg -i gnuplot_4.6.6-3_all.deb

# app dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
# app dev dependencies
COPY requirements-dev.txt requirements-dev.txt
RUN pip install -r requirements-dev.txt
# cleanup
RUN rm -rf gnuplot_4.6.6-3_all.deb \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /usr/share/doc && rm -rf /usr/share/man \
  && apt-get purge -y --auto-remove ${BUILD_DEPS} \
  && apt-get clean

COPY . .

CMD ["watchmedo", "auto-restart", "--directory=./", "--pattern=*.py", "--recursive", "--", "celery", "-A", "main", "worker", "--loglevel=info"]