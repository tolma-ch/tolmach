FROM python:3.9-slim-bullseye

USER root
RUN apt update && apt install -q -y nodejs npm supervisor default-libmysqlclient-dev gettext wget unzip \
    libreoffice-core-nogui libreoffice-writer-nogui libreoffice-calc-nogui libreoffice-java-common default-jre && \
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

RUN echo user=root >>  /etc/supervisor/supervisord.conf
COPY .build/supervisor_include.conf /etc/supervisor/conf.d/tolmach.conf
COPY .build/tolmach.ini /etc/tolmach.ini
COPY .build/mime.types /etc/mime.types
COPY ./requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt && python -m nltk.downloader -d /usr/share/nltk_data punkt

COPY . /var/www/tolma.ch

ENV HOME=/var/www
WORKDIR /var/www/tolma.ch
RUN npm install && npm run fetch-vendors && npm run build
RUN django-admin compilemessages

EXPOSE 7000
EXPOSE 8000

CMD ["/usr/bin/supervisord", "-n"]
