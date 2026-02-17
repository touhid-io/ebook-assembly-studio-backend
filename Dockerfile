# Python Image
FROM python:3.10-slim

# ফন্ট এবং লাইব্রেরি ইন্সটল (বাংলা ফন্টসহ)
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    libffi-dev \
    fonts-noto \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-beng \
    fonts-beng-extra \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# ফন্ট ক্যাশ রিফ্রেশ
RUN fc-cache -f -v

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "backend:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
