# Dockerfile 
FROM python:3.10-slim

WORKDIR /app

COPY src/ ./src/
COPY models/ ./models/
COPY data/   ./data/

RUN pip install --no-cache-dir flask dnspython prometheus_client joblib scikit-learn pandas numpy

EXPOSE 8053 9091

CMD ["python", "src/dns_resolver.py"]
