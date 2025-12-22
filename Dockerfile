FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (kept minimal; add build-essential if you add compiled deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend
COPY README.md /app/README.md

ENV HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=info

EXPOSE 8000

CMD ["python", "-m", "backend.run"]

