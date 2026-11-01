FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY requirements-data-lake.txt requirements-market-data.txt ./
RUN pip install --no-cache-dir -r requirements-data-lake.txt -r requirements-market-data.txt \
    && useradd --system --uid 10001 --no-create-home lakeapp
COPY market_data ./market_data
COPY futures_intelligence ./futures_intelligence
COPY pipeline ./pipeline
COPY data_lake ./data_lake
COPY deploy/data-lake/runtime.py ./deploy/data-lake/runtime.py
USER 10001
ENTRYPOINT ["python", "/app/deploy/data-lake/runtime.py"]
CMD ["api"]
