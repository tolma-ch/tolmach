FROM python:3.9-slim-bullseye

USER root
RUN apt update && apt install -q -y nodejs npm supervisor default-libmysqlclient-dev gettext wget unzip \
    libreoffice-core-nogui libreoffice-writer-nogui libreoffice-calc-nogui libreoffice-java-common default-jre && \
    wget -O /opt/okapi.zip "https://okapiframework.org/binaries/main/1.43.0/okapi-lib_all-platforms_1.43.0.zip" && \
    cd /opt && unzip okapi.zip -d okapi && rm -f okapi.zip
# RUN yum install -y epel-release && yum install -y libreoffice-core libreoffice-writer libreoffice-calc supervisor nodejs npm && \
#     yum clean all && \
#     rm -rf /var/cache/yum && \
#     wget -O /usr/bin/sdcv megavenik.ru/sdcv && chmod +x /usr/bin/sdcv && mkdir /usr/share/dicts && \

RUN npm install -g inherits coffee-script grunt grunt-cli

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
RUN npm install && grunt
RUN django-admin compilemessages

EXPOSE 7000
EXPOSE 8000

CMD ["/usr/bin/supervisord", "-n"]
