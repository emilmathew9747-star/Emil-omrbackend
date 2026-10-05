FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV AUDIVERIS_VERSION=5.3.1
ENV PORT=10000

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    ca-certificates \
    openjdk-17-jre \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN wget -q \
    "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb" \
    -O /tmp/audiveris.deb \
    && apt-get update \
    && apt-get install -y /tmp/audiveris.deb \
    && rm -f /tmp/audiveris.deb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
