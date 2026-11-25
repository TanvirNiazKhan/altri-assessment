FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so code edits don't bust the layer cache.
ARG INSTALL_EXTRAS=dev
COPY pyproject.toml ./
RUN mkdir src && touch src/__init__.py \
    && pip install -e ".[${INSTALL_EXTRAS}]"

COPY . .

RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["./scripts/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
