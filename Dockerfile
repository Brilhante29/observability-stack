FROM python:3.12.13-slim@sha256:423ed6ab25b1921a477529254bfeeabf5855151dc2c3141699a1bfc852199fbf

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY constraints.lock requirements.txt ./
RUN pip install --no-cache-dir --disable-pip-version-check --requirement requirements.txt \
    && addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --gid 10001 --home /nonexistent --no-create-home app

COPY src ./src
RUN mkdir --parents /output && chown --recursive 10001:10001 /output

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=2s --start-period=5s --retries=10 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=1)"]

ENTRYPOINT ["python", "-m", "observability_stack.cli"]
