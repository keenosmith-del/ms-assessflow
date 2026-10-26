FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.runtime.lock ./
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.runtime.lock && useradd --uid 10001 --create-home assessflow
COPY pyproject.toml ./
COPY app ./app
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-deps .
COPY alembic.ini ./
COPY migrations ./migrations
USER assessflow
EXPOSE 5050
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5050", "--no-access-log"]
