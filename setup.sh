#!/bin/bash
set -e

echo "🚀 Faust Streaming Project Setup"
echo "=================================="

# Kiểm tra Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker không được cài đặt"
    exit 1
fi

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 không được cài đặt"
    exit 1
fi

echo ""
echo "📦 Bước 1: Cài đặt Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🐳 Bước 2: Khởi động Kafka + Zookeeper..."
docker-compose up -d

echo ""
echo "⏳ Chờ Kafka khởi động..."
sleep 3

echo ""
echo "✅ Setup hoàn tất!"
echo ""
echo "📋 Lệnh chạy:"
echo "   Terminal 1 (App cơ bản): faust -A app_base worker -l info"
echo "   Terminal 2 (DLQ): faust -A feature1_dlq worker -l info"
echo "   Terminal 3 (Metrics): faust -A feature2_metrics worker -l info"
echo "   Terminal 4 (Producer): python producer.py -n 30 -i 0.8"
echo ""
echo "🌐 Truy cập dashboard:"
echo "   http://localhost:6066/dashboard"
echo ""
echo "🛑 Dừng Kafka: docker-compose down"
echo ""
