FROM python:3.12.14-slim-trixie@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea

RUN apt-get update && apt-get upgrade --yes && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY constraints.lock requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check --requirement requirements.txt \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --gid 10001 --home /nonexistent --no-create-home app

COPY src ./src
RUN mkdir --parents /evidence /output \
    && chown --recursive 10001:10001 /evidence /output

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=2s --start-period=5s --retries=10 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=1)"]

ENTRYPOINT ["python", "-m", "observability_stack.cli"]
