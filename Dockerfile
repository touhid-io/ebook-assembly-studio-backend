# Python Image ব্যবহার করছি
FROM python:3.10-slim

# ১. বাংলা ফন্ট এবং সিস্টেম লাইব্রেরি ইনস্টল করা (সবচেয়ে গুরুত্বপূর্ণ ধাপ)
# এখানে fonts-beng, fonts-noto, fonts-liberation যোগ করা হয়েছে যা পিংক বক্স দূর করবে
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

# ফন্ট ক্যাশ রিফ্রেশ করা (যাতে সার্ভার নতুন ফন্টগুলো চিনতে পারে)
RUN fc-cache -f -v

# ওয়ার্কিং ডিরেক্টরি সেট করা
WORKDIR /app

# রিকোয়ারমেন্টস কপি ও ইন্সটল করা
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# বাকি সব কোড কপি করা
COPY . .

# পোর্ট এক্সপোজ করা
EXPOSE 10000

# Gunicorn দিয়ে সার্ভার স্টার্ট করা
CMD ["gunicorn", "backend:app", "--bind", "0.0.0.0:10000", "--timeout", "120"]
