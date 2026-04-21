FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    findutils \
    md5deep \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir Pillow --break-system-packages

WORKDIR /workspace

COPY gen_inputs.py /workspace/gen_inputs.py
COPY setup.sh /workspace/setup.sh

RUN chmod +x /workspace/setup.sh && sed -i 's/^ \{1\}def /def /' /workspace/gen_inputs.py && python /workspace/gen_inputs.py

CMD ["bash"]