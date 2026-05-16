FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    nltk \
    regex \
    chardet \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN python -c "\
import nltk, ssl, os; \
os.environ.setdefault('NLTK_DATA', '/usr/share/nltk_data'); \
try: \
    _create_unverified_https_context = ssl._create_unverified_context; \
except AttributeError: \
    pass; \
else: \
    ssl._create_default_https_context = _create_unverified_https_context; \
nltk.download('punkt', download_dir='/usr/share/nltk_data', quiet=True, raise_on_error=False); \
nltk.download('punkt_tab', download_dir='/usr/share/nltk_data', quiet=True, raise_on_error=False); \
nltk.download('stopwords', download_dir='/usr/share/nltk_data', quiet=True, raise_on_error=False) \
" || echo "NLTK download failed, continuing without NLTK data"