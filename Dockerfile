FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
ARG AUDIVERIS_VERSION=5.11.0
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates wget python3 python3-pip && rm -rf /var/lib/apt/lists/*
RUN wget -q "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb" -O /tmp/audiveris.deb \
    && apt-get update && apt-get install -y /tmp/audiveris.deb \
    && rm -f /tmp/audiveris.deb && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
COPY main.py .
ENV PORT=10000
EXPOSE 10000
CMD ["sh","-c","uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
