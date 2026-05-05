FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e ".[dev]" && pip install uvicorn[standard]

COPY app/ app/
COPY conf/ conf/
RUN mkdir -p logs

EXPOSE 8000

HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]