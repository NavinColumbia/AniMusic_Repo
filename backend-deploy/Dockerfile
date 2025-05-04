#FROM python:3.12-slim had  errors somethimes so switched to below

FROM docker.io/library/python:3.12-slim

RUN apt-get update \
 && apt-get install -y build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app          ./app
COPY data         ./data
COPY model_files  ./model_files

COPY static       ./static

ENV PORT=8080
CMD sh -c "gunicorn --preload \
           -k uvicorn.workers.UvicornWorker \
           -w 2 -b 0.0.0.0:${PORT} app.main:app"

