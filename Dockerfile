FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV AUDIVERIS_VERSION=5.3.1

RUN apt-get update && apt-get install -y \
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
    && dpkg -i /tmp/audiveris.deb || apt-get -f install -y \
    && rm -f /tmp/audiveris.deb

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV PORT=10000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
