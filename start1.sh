#!/bin/bash

set -e

echo "Checking Python..."
PYTHON=$(which python3 || true)
if [ -z "$PYTHON" ]; then
    echo "Python3 not found. Please install Python 3.10+"
    exit 1
fi

echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi

# Activate venv in macOS/Linux
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "Could not activate virtual environment. 'activate' script not found."
    exit 1
fi
echo "Virtual environment activated"

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "Python packages installed"

echo "Training ML model..."
python3 src/ml_engine.py
echo "ML model trained"

echo "Starting services..."
nohup python3 src/upstream_monitor.py > logs/upstream_monitor.log 2>&1 &
sleep 2
nohup python3 src/dns_resolver.py > logs/dns_resolver.log 2>&1 &
sleep 2
echo " Python services running"

echo "Preparing Docker environment..."
docker compose down -v || true
docker pull grafana/grafana:latest
docker pull prom/prometheus:latest
docker compose up -d --build
echo "Docker services up"

echo ""
echo "Access your services:"
echo "Grafana:     http://localhost:3000"
echo "Prometheus:  http://localhost:9090"
echo "DNS Resolver: http://localhost:8053/resolve?domain=example.com&type=A"
echo "To run Locust benchmarking:"
echo "locust -f locustfile.py --host=http://localhost:8053"
