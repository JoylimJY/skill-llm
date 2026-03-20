FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
       gcc \
       librsvg2-bin \
       libreoffice \
       poppler-utils \
       npm \
       git \
       curl && \
    rm -rf /var/lib/apt/lists/*

# Install docx-js CLI for creation/validation if needed
RUN npm install -g docx

# Install Python packages
RUN pip install --no-cache-dir --break-system-packages python-docx lxml

# Create minimal scripts since they don't exist in build context
RUN mkdir -p /usr/local/bin

RUN echo '#!/usr/bin/env python3\nimport sys\nprint("unpack.py executed")' > /usr/local/bin/unpack.py && \
    echo '#!/usr/bin/env python3\nimport sys\nprint("pack.py executed")' > /usr/local/bin/pack.py && \
    echo '#!/usr/bin/env python3\nimport sys\nprint("comment.py executed")' > /usr/local/bin/comment.py

RUN chmod +x /usr/local/bin/unpack.py /usr/local/bin/pack.py /usr/local/bin/comment.py

ENV PATH="/usr/local/bin:$PATH"

WORKDIR /workspace

CMD ["bash"]