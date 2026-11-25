# Servizio OCR dei cartelloni con l'API Gemini (service.py). Nessun modello locale: niente Ollama.
# Contesto di build: la cartella helper/OCR (serve anche il codice della V4, che questa versione riusa):
#   docker build -f V5-Gemini/Dockerfile helper/OCR      (oppure deploy/compose.yaml, profilo ocr-gemini)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    OCR_V4_DIR=/app/V4-AI

# tzdata: con TZ=Europe/Rome l'anno del cartellone si deduce dalla data italiana
# ca-certificates: HTTPS verso generativelanguage.googleapis.com
RUN apt-get update && apt-get install -y --no-install-recommends tzdata ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/V5-Gemini
COPY V5-Gemini/requirements.txt .
RUN pip install -r requirements.txt

# dalla V4 solo regole e dati (segmentazione, parser, validatori, elenchi): stessa struttura di cartelle del repo
COPY V4-AI/config.json /app/V4-AI/
COPY V4-AI/orario /app/V4-AI/orario
COPY V4-AI/elenchi /app/V4-AI/elenchi
COPY V4-AI/schema /app/V4-AI/schema

COPY V5-Gemini/config.json V5-Gemini/main.py V5-Gemini/service.py ./
COPY V5-Gemini/gemini_ocr ./gemini_ocr

RUN useradd --system --uid 10003 --no-create-home --shell /usr/sbin/nologin ocr
USER ocr

EXPOSE 8090
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request as u; u.urlopen('http://127.0.0.1:8090/health', timeout=4)"]
CMD ["uvicorn", "service:build", "--factory", "--host", "0.0.0.0", "--port", "8090", \
     "--no-server-header", "--timeout-keep-alive", "5", "--limit-concurrency", "8"]
