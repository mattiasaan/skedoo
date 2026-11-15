# Immagine del backend: la stessa per l'API (uvicorn) e per il worker della bacheca (deploy/compose.yaml).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# tzdata: con TZ=Europe/Rome le date "di oggi" (variazioni passate, log) sono quelle italiane
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# utente senza privilegi; /app/data è il volume con i dati della bacheca (scritto solo dal worker)
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin skedoo \
 && mkdir -p /app/data && chown skedoo:skedoo /app/data
USER skedoo

EXPOSE 8000
# una sola istanza: sessioni e rate limit sono in memoria
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
     "--no-server-header", "--no-proxy-headers", "--timeout-keep-alive", "5"]
