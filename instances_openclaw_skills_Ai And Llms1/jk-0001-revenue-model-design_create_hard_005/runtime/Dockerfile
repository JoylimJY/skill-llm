FROM python:3.11-slim
RUN pip install --break-system-packages --no-cache-dir pandas openpyxl PyPDF2 python-docx
RUN mkdir -p /workspace
RUN printf '%s\n' '#!/bin/bash' 'set -e' 'chmod +x /workspace || true' > /workspace/setup.sh && chmod +x /workspace/setup.sh
RUN printf '%s\n' "from pathlib import Path" "from openpyxl import Workbook" "from docx import Document" "from PyPDF2 import PdfWriter" "" "base = Path('.') " > /workspace/gen_inputs.py