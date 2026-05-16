FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
    nltk \
    textstat \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN python -c "\
import nltk, ssl, urllib.request; \
nltk.data.path.insert(0, '/usr/share/nltk_data'); \
import os; os.makedirs('/usr/share/nltk_data', exist_ok=True); \
try: \
    nltk.download('punkt', download_dir='/usr/share/nltk_data', quiet=True, raise_on_error=True); \
    nltk.download('punkt_tab', download_dir='/usr/share/nltk_data', quiet=True, raise_on_error=True); \
    nltk.download('stopwords', download_dir='/usr/share/nltk_data', quiet=True, raise_on_error=True); \
except Exception as e: \
    print(f'NLTK download skipped: {e}'); \
" || echo "NLTK downloads failed, continuing without corpora"