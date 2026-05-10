FROM node:18-bullseye

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir \
    pathlib \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /workspace

# Copy skill context will be volume-mounted or copied externally
RUN mkdir -p /workspace/skill_context

# Install skill dependencies
COPY --from=node:18-bullseye /usr/local/lib/node_modules /usr/local/lib/node_modules