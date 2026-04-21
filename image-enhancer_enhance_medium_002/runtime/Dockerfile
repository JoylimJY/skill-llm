FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages opencv-python-headless Pillow numpy scikit-image

WORKDIR /workspace

RUN python - <<'PY'
from PIL import Image, ImageDraw
Image.draw = ImageDraw
PY