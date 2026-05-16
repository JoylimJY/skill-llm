FROM debian:bookworm-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for eval and input generation
RUN pip3 install duckdb pandas pyarrow --break-system-packages -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create a duckdb CLI wrapper using the installed Python duckdb package
RUN printf '#!/usr/bin/env python3\nimport sys\nimport duckdb\nfrom duckdb.shell import shell\nshell()\n' > /usr/local/bin/duckdb_py_wrapper.py \
    && chmod +x /usr/local/bin/duckdb_py_wrapper.py

# Install duckdb CLI via the duckdb pip package's bundled CLI
RUN python3 -c "import duckdb, os, shutil; cli = os.path.join(os.path.dirname(duckdb.__file__), 'duckdb'); shutil.copy(cli, '/usr/local/bin/duckdb') if os.path.exists(cli) else None" || true

# If CLI not bundled, create a shell wrapper
RUN if [ ! -f /usr/local/bin/duckdb ] || [ ! -s /usr/local/bin/duckdb ]; then \
    printf '#!/bin/bash\npython3 -c "import duckdb; con = duckdb.connect(); import sys; [con.execute(l) for l in sys.stdin]" "$@"\n' > /usr/local/bin/duckdb; \
    chmod +x /usr/local/bin/duckdb; \
    fi

RUN chmod +x /usr/local/bin/duckdb

WORKDIR /workspace