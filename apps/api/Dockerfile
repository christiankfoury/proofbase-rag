FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system proofbase \
    && useradd --system --gid proofbase --home-dir /app --shell /usr/sbin/nologin proofbase

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=proofbase:proofbase apps ./apps
COPY --chown=proofbase:proofbase data ./data
COPY --chown=proofbase:proofbase docs ./docs
COPY --chown=proofbase:proofbase scripts ./scripts

USER proofbase

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read()"

CMD ["uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
