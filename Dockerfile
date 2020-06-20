FROM python:3.6

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
RUN apt-get update && \
    apt-get install -y build-essential python-dev libmariadb-dev-compat \
    supervisor libreoffice-common \
    nodejs
RUN npm install -g inherits coffeescript grunt grunt-cli

RUN sed '/st_mysql_options options;/a unsigned int reconnect;' /usr/include/mysql/mysql.h -i.bkp
RUN useradd -b /var -d /var/www -ms /bin/bash www
RUN mkdir /var/log/tolma.ch && chown -R www: /var/log/tolma.ch

COPY .build/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY .build/tolmach.ini /etc/tolmach.ini
COPY . /var/www/tolma.ch
RUN chown -R www: /var/www/tolma.ch

WORKDIR /var/www/tolma.ch

RUN pip3 install -r requirements.txt
RUN pip3 install -r chtec/requirements.txt
RUN python -m nltk.downloader -d /usr/share/nltk_data punkt

USER www
RUN npm install && grunt

USER root

EXPOSE 7000
EXPOSE 8000

CMD ["/usr/bin/supervisord"]