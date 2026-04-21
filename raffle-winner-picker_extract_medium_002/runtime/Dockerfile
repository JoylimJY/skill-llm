FROM python:3.11-slim

ENV http_proxy= \
    https_proxy= \
    HTTP_PROXY= \
    HTTPS_PROXY= \
    all_proxy= \
    ALL_PROXY=

RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's@http://deb.debian.org/debian@https://mirrors.aliyun.com/debian@g' /etc/apt/sources.list.d/debian.sources; \
      sed -i 's@http://deb.debian.org/debian-security@https://mirrors.aliyun.com/debian-security@g' /etc/apt/sources.list.d/debian.sources; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    --no-cache-dir \
    --default-timeout=120 \
    -i https://mirrors.aliyun.com/pypi/simple \
    openpyxl

# No additional scripts copied; framework mounts dynamically