FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    requests \
    PyYAML \
    markdown \
    beautifulsoup4 \
    python-dateutil \
    jsonschema

WORKDIR /workspace
COPY . .

RUN if [ -f "gen_inputs.py" ]; then cp gen_inputs.py gen_inputs_script && chmod +x gen_inputs_script; fi
RUN if [ -f "eval.py" ]; then cp eval.py eval_script && chmod +x eval_script; else touch eval_script && chmod +x eval_script; fi

CMD ["/bin/bash"]