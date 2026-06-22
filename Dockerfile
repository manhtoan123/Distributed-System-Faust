FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY models.py .
COPY app_base.py .
COPY feature1_dlq.py .
COPY feature2_metrics.py .
COPY producer.py .

CMD ["faust", "-A", "app_base", "worker", "-l", "info"]
