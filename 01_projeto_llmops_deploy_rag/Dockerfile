FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2.8,<3"

COPY solucao ./solucao
COPY data ./data

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    RAG_TOP_K=3

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "solucao.app_solution:app", "--host", "0.0.0.0", "--port", "8000"]
