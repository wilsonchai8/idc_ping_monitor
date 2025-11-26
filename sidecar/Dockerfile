FROM docker.m.daocloud.io/ubuntu:22.04

WORKDIR /app

ADD sources.list /etc/apt/sources.list

RUN apt update && apt install -y --no-install-recommends \
    rrdtool \
    librrd-dev \
    gcc \
    make \
    python3-dev \
    python3 \
    python3-pip \
    cron \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install prometheus_client requests rrdtool pypinyin -i https://pypi.tuna.tsinghua.edu.cn/simple
ADD app /app
ADD ips /opt/ips
ADD crontab /etc/crontab
ADD entrypoint.sh /entrypoint.sh

CMD ["/entrypoint.sh"]
