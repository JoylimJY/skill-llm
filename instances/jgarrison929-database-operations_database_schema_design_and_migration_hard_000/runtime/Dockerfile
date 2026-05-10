FROM postgres:15-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-psycopg2 \
    postgresql-client \
    sudo \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install psycopg2-binary -i https://pypi.tuna.tsinghua.edu.cn/simple

ENV POSTGRES_PASSWORD=testpassword
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=ecommerce_db