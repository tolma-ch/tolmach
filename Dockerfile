# Node.js is only needed to build the frontend assets, so it is taken from the
# official image instead of Debian's ancient packages.
FROM node:22-trixie-slim AS node

FROM python:3.9-slim-trixie

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential pkg-config \
        supervisor default-libmysqlclient-dev gettext wget unzip ca-certificates \
        libreoffice-core-nogui libreoffice-writer-nogui libreoffice-calc-nogui \
        libreoffice-java-common default-jre && \
    rm -rf /var/lib/apt/lists/* && \
    wget -O /opt/okapi.zip "https://okapiframework.org/binaries/main/1.43.0/okapi-lib_all-platforms_1.43.0.zip" && \
    cd /opt && unzip okapi.zip -d okapi && rm -f okapi.zip

# Modern Node.js + npm (Debian's are far too old and slow for the asset build).
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -sf ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx && \
    node --version && npm --version

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

RUN echo user=root >>  /etc/supervisor/supervisord.conf
COPY .build/supervisor_include.conf /etc/supervisor/conf.d/tolmach.conf
COPY .build/tolmach.ini /etc/tolmach.ini
COPY .build/mime.types /etc/mime.types
COPY ./requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt && python -m nltk.downloader -d /usr/share/nltk_data punkt punkt_tab

ENV HOME=/var/www
WORKDIR /var/www/tolma.ch

# Install JS dependencies in a dedicated layer so it is only rebuilt when the
# manifests change, not on every source edit.
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . /var/www/tolma.ch
RUN npm run fetch-vendors && npm run build
RUN python manage.py compilemessages

EXPOSE 7000
EXPOSE 8000

CMD ["/usr/bin/supervisord", "-n"]
