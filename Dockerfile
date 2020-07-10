FROM centos/python-36-centos7:20200624-7b63bb4

USER root
RUN yum install -y epel-release && yum install -y libreoffice-core libreoffice-writer libreoffice-calc supervisor && \
    yum clean all && \
    rm -rf /var/cache/yum
RUN wget https://nodejs.org/dist/latest-v12.x/node-v12.18.2-linux-x64.tar.gz && \
    tar --strip-components 1 -xzvf node-v* -C /usr/local && \
    rm -f node-v12.18.2-linux-x64.tar.gz && \
    npm install -g inherits coffee-script grunt grunt-cli
RUN useradd -b /var -d /var/www -ms /bin/bash www && \
    mkdir /var/log/tolma.ch && chown -R www: /var/log/tolma.ch

COPY .build/supervisord.conf /etc/supervisord.conf
COPY .build/tolmach.ini /etc/tolmach.ini
COPY ./requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt && python -m nltk.downloader -d /usr/share/nltk_data punkt

COPY . /var/www/tolma.ch
RUN chown -R www: /var/www/tolma.ch

USER www
ENV HOME=/var/www
WORKDIR /var/www/tolma.ch
RUN npm install && grunt

USER root

EXPOSE 7000
EXPOSE 8000

CMD ["/usr/bin/supervisord"]