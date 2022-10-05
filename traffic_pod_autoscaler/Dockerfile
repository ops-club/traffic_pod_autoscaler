FROM python:3.10-slim-bullseye

RUN apt-get update && \
  apt-get install -y \
  zip \
  curl \
  wget \
  && pip3 install --upgrade pip \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src /app/src
WORKDIR /app/src
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "-u", "main.py"]
