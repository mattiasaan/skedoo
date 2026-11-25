# Servizio OCR dei cartelloni (service.py). Il modello gira nel container Ollama (deploy/compose.yaml).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# tzdata: con TZ=Europe/Rome l'anno del cartellone si deduce dalla data italiana
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-service.txt .
RUN pip install -r requirements-service.txt

COPY config.json main.py service.py ./
COPY orario ./orario
COPY elenchi ./elenchi
COPY schema ./schema

RUN useradd --system --uid 10002 --no-create-home --shell /usr/sbin/nologin ocr
USER ocr

EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8090/health', timeout=4)"]
CMD ["uvicorn", "service:build", "--factory", "--host", "0.0.0.0", "--port", "8090", \
     "--no-server-header", "--timeout-keep-alive", "5", "--limit-concurrency", "8"]
