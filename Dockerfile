FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PORT=10000

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir "homr[cpu]" fastapi uvicorn python-multipart

COPY main.py .

EXPOSE 10000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
