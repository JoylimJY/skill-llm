FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    sed \
    gawk \
    python3 \
    python3-pip \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install translate-shell via npm as it's available cross-platform
RUN npm install -g translate-shell 2>/dev/null || true

# Install translate-shell from source (the canonical way on Linux)
RUN wget -q --timeout=30 --tries=2 https://raw.githubusercontent.com/soimort/translate-shell/gh-pages/trans -O /usr/local/bin/trans \
    && chmod +x /usr/local/bin/trans \
    || (curl -sL --max-time 30 https://git.io/trans -o /usr/local/bin/trans && chmod +x /usr/local/bin/trans) \
    || true

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages

WORKDIR /workspace