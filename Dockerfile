# Dockerfile pour JDGF-LAB-FRAMEWORK
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/root/.cache/uv

WORKDIR /app

# Installation de uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copie des fichiers de dépendances
COPY pyproject.toml uv.lock ./

# Installation des dépendances
RUN uv sync --frozen --no-dev

# Copie du code source
COPY src/ ./src/
COPY scripts/ ./scripts/

# Exposition des ports (ajuste selon tes services)
EXPOSE 8000 8501

# Commande par défaut
CMD ["uv", "run", "python", "-m", "jdgf_framework.cli"]

# Healthcheck (optionnel)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD uv run python -c "import jdgf_framework; print('OK')"
