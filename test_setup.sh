#!/bin/bash
# test_setup.sh — Kiểm tra setup có hoàn tất chưa

set -e

echo "🧪 Testing Faust Setup..."
echo "========================="

# 1. Kiểm tra Python
echo "✓ Checking Python..."
python --version

# 2. Kiểm tra Faust
echo "✓ Checking Faust..."
python -c "import faust; print(f'  Faust version: {faust.__version__}')"

# 3. Kiểm tra Kafka
echo "✓ Checking Kafka connection..."
python -c "
from kafka import KafkaProducer
import sys
try:
    producer = KafkaProducer(bootstrap_servers='localhost:9092', request_timeout_ms=5000)
    producer.close()
    print('  Kafka is running ✓')
except Exception as e:
    print(f'  Kafka ERROR: {e}')
    print('  Run: docker-compose up -d')
    sys.exit(1)
"

# 4. Kiểm tra models
echo "✓ Checking models..."
python -c "from models import Order; print(f'  Order model loaded ✓')"

# 5. Kiểm tra apps
echo "✓ Checking apps..."
python -c "import app_base; print('  app_base.py loaded ✓')"
python -c "import feature1_dlq; print('  feature1_dlq.py loaded ✓')"
python -c "import feature2_metrics; print('  feature2_metrics.py loaded ✓')"

# 6. Kiểm tra producer
echo "✓ Checking producer..."
python -c "import producer; print('  producer.py loaded ✓')"

# 7. Kiểm tra Docker
echo "✓ Checking Docker containers..."
docker ps | grep faust- | while read line; do
    echo "  - $line"
done

echo ""
echo "✅ All checks passed!"
echo ""
echo "🚀 Ready to start:"
echo ""
echo "Terminal 1: faust -A app_base worker -l info"
echo "Terminal 2: faust -A app_base worker -l info --web-port 6067"
echo "Terminal 3: python producer.py -n 15 -i 0.8"
echo ""
