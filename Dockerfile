FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

RUN pip install --no-cache-dir uv \
    && groupadd --system app \
    && useradd --system --gid app --create-home app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev

COPY app ./app

RUN chown -R app:app /app /opt/venv

USER app

CMD ["/opt/venv/bin/python", "-m", "app.main"]
