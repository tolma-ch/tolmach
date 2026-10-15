# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Frontend assets
#
# Node is only needed to build the static assets, so it lives in its own stage
# and never ends up in the runtime image (saves node, npm and node_modules —
# roughly 350 MB).
# ---------------------------------------------------------------------------
FROM node:22-trixie-slim AS assets
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY scripts ./scripts
COPY tolmach/static ./tolmach/static
COPY templates ./templates
RUN npm run fetch-vendors && npm run build

# ---------------------------------------------------------------------------
# Python wheels
#
# The compiler toolchain and headers are only needed while building mysqlclient
# and uWSGI, so build wheels here and keep build-essential out of the runtime.
# ---------------------------------------------------------------------------
FROM python:3.9-slim-trixie AS pybuilder
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*
COPY ./requirements.txt /requirements.txt
# Long timeout/retries: the PyPI CDN can be slow and some deps only ship sdists.
RUN PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10 \
    pip3 wheel --no-cache-dir --prefer-binary -w /wheels -r /requirements.txt

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
FROM python:3.9-slim-trixie

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        supervisor default-libmysqlclient-dev gettext wget unzip ca-certificates \
        libreoffice-core-nogui libreoffice-writer-nogui libreoffice-calc-nogui \
        libreoffice-java-common default-jre && \
    rm -rf /var/lib/apt/lists/* && \
    wget -O /opt/okapi.zip "https://okapiframework.org/binaries/main/1.43.0/okapi-lib_all-platforms_1.43.0.zip" && \
    cd /opt && unzip okapi.zip -d okapi && rm -f okapi.zip

RUN /bin/bash -c 'ARCH=`uname -m` && \
    if [ "$ARCH" == "x86_64" ]; then \
       echo "Current arch is x86_64" && \
       wget -O /usr/bin/sdcv megavenik.ru/sdcv/sdcv-x86_64 && chmod +x /usr/bin/sdcv && mkdir /usr/share/dicts; \
    elif [ "$ARCH" == "aarch64" ]; then \
       echo "Current arch is aarch64" && \
       wget -O /usr/bin/sdcv megavenik.ru/sdcv/sdcv-aarch64 && chmod +x /usr/bin/sdcv && mkdir /usr/share/dicts; \
    else \
       echo "Unknown arch, wont install sdcv"; \
    fi' && ln -s /lib/x86_64-linux-gnu/libreadline.so.8 /lib/x86_64-linux-gnu/libreadline.so.6

RUN mkdir /var/www /var/log/tolma.ch

RUN echo user=root >> /etc/supervisor/supervisord.conf
COPY .build/supervisor_include.conf /etc/supervisor/conf.d/tolmach.conf
COPY .build/tolmach.ini /etc/tolmach.ini
COPY .build/mime.types /etc/mime.types
COPY ./requirements.txt /requirements.txt

# Install from the wheels built in `pybuilder`. They are bind-mounted, not
# copied, so they do not add a layer to the final image.
RUN --mount=type=bind,from=pybuilder,source=/wheels,target=/wheels \
    PIP_DEFAULT_TIMEOUT=120 PIP_RETRIES=10 \
    pip3 install --no-cache-dir --no-index --find-links=/wheels -r /requirements.txt && \
    python -m nltk.downloader -d /usr/share/nltk_data punkt punkt_tab

ENV HOME=/var/www
WORKDIR /var/www/tolma.ch

COPY . /var/www/tolma.ch
# Generated frontend assets (gitignored; built in the `assets` stage above).
COPY --from=assets /src/tolmach/static/assets/ /var/www/tolma.ch/tolmach/static/assets/
COPY --from=assets /src/tolmach/static/dist/ /var/www/tolma.ch/tolmach/static/dist/
COPY --from=assets /src/tolmach/static/js/ /var/www/tolma.ch/tolmach/static/js/
# build.js rewrites front_version in templates/main/base.html for cache busting.
COPY --from=assets /src/templates/ /var/www/tolma.ch/templates/

RUN python manage.py compilemessages

EXPOSE 7000
EXPOSE 8000

CMD ["/usr/bin/supervisord", "-n"]
