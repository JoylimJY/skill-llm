FROM python:3.11-slim
WORKDIR /workspace
COPY gen_inputs.py ./gen_inputs_script.py
RUN pip install --break-system-packages --default-timeout=120 python-docx && pip cache purge