# 🚀 Quick Start Guide

## Cài đặt nhanh (2 phút)

```bash
# 1. Cài Python dependencies
pip install -r requirements.txt

# 2. Khởi động Kafka
docker-compose up -d

# 3. Kiểm tra Kafka sẵn sàng
sleep 3
docker ps  # Nên thấy faust-kafka và faust-zookeeper running
```

---

## Demo cơ bản (5 phút)

**Terminal 1: Worker 1**
```bash
faust -A app_base worker -l info
```

**Terminal 2: Worker 2** (để demo phân tán)
```bash
faust -A app_base worker -l info --web-port 6067
```

**Terminal 3: Gửi data**
```bash
python producer.py -n 15 -i 0.8
```

→ Sẽ thấy 2 workers xử lý orders và chia sẻ state qua Faust Tables

---

## Demo DLQ (Dead Letter Queue) — 10 phút

Minh họa: message thất bại → retry với exponential backoff → DLQ alert

**Terminal 1:**
```bash
faust -A feature1_dlq worker -l info
```

**Terminal 2:**
```bash
faust -A feature1_dlq worker -l info --web-port 6067
```

**Terminal 3:** Gửi với 40% fail-rate
```bash
python producer.py -n 20 -i 1.5 -f 0.4
```

→ Thấy retry logic: FAIL → retry 1 (chờ 2s) → retry 2 (chờ 4s) → retry 3 (chờ 8s) → DLQ

---

## Demo Metrics Dashboard — 10 phút

Real-time metrics + interactive charts

**Terminal 1:**
```bash
faust -A feature2_metrics worker -l info
```

**Terminal 2:**
```bash
faust -A feature2_metrics worker -l info --web-port 6067
```

**Terminal 3:** Gửi liên tục
```bash
python producer.py -n 50 -i 0.5
```

**Mở trình duyệt:**
```
http://localhost:6066/dashboard
```

→ Thấy dashboard tự-refresh, biểu đồ, metrics API

---

## Cấu trúc file chính

```
models.py              # Data models (Order)
├─ Order: order_id, user_id, product, quantity, price, retry_count, error_message

app_base.py            # Demo 3 khái niệm: Topic, Agent, Table
├─ orders_topic
├─ order_count_by_user (Table)
├─ total_revenue (Table)
└─ process_orders (Agent)

feature1_dlq.py        # DLQ + Exponential Backoff
├─ orders_topic → main_processor
├─ orders_retry (topic)
│  └─ retry_processor
├─ orders_dlq (topic)
│  └─ dlq_monitor
└─ dlq_stats (Table)

feature2_metrics.py    # Distributed Metrics + Dashboard
├─ orders_topic → metrics_collector (Agent)
├─ Tables: global_stats, orders_by_user, revenue_by_prod, orders_by_prod, throughput
├─ API: /metrics/summary, /metrics/users, /metrics/products, /metrics/throughput
└─ Dashboard: GET /dashboard (HTML + Chart.js)

producer.py            # Test data generator
└─ Gửi random orders vào 'orders' topic
```

---

## Key Concepts

### Topic
```python
orders_topic = app.topic('orders', value_type=Order)
# → Kafka topic + auto serialization
```

### Agent
```python
@app.agent(orders_topic)
async def process_orders(stream):
    async for order in stream:
        # Xử lý, tất cả workers chia sẻ
```

### Table (Distributed State)
```python
order_count_by_user = app.Table('order_count_by_user', default=int)
order_count_by_user['user_1'] += 1
# → Tất cả workers thấy được value này (sync qua Kafka changelog)
```

---

## Lệnh hay dùng

```bash
# Khởi động Kafka
docker-compose up -d

# Dừng Kafka
docker-compose down

# Xem logs Kafka
docker-compose logs -f kafka

# Chạy worker
faust -A app_name worker -l info

# Chạy worker + thay đổi web port
faust -A app_name worker -l info --web-port 6070

# Gửi 20 orders, 1s giữa mỗi cái, 20% fail-rate
python producer.py -n 20 -i 1.0 -f 0.2

# Gửi 100 orders, 0.5s giữa mỗi cái, 0% fail
python producer.py -n 100 -i 0.5 -f 0

# Xem messages trong Kafka topic
docker exec faust-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic orders \
    --from-beginning
```

---

## URLs quan trọng

| URL | Mô tả |
|-----|-------|
| `http://localhost:6066/dashboard` | Metrics dashboard (feature2) |
| `http://localhost:6066/metrics/summary` | API: tóm tắt metrics |
| `http://localhost:6066/metrics/users` | API: theo user |
| `http://localhost:6066/metrics/products` | API: theo sản phẩm |
| `http://localhost:6066/metrics/throughput` | API: throughput/phút |

---

## Troubleshooting nhanh

```bash
# Kafka không chạy?
docker-compose ps
docker-compose up -d

# Lỗi "no module named faust"?
pip install faust-streaming

# Port 6066 đang dùng?
faust -A feature2_metrics worker --web-port 6070

# Xem Kafka topics
docker exec faust-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

## So sánh 3 ứng dụng

```
┌─────────────────┬──────────┬────────────┬─────────────┐
│ Tính năng       │ app_base │ feature1   │ feature2    │
├─────────────────┼──────────┼────────────┼─────────────┤
│ Topics          │ 1        │ 3          │ 1           │
│ Tables          │ 3        │ 4          │ 5           │
│ DLQ             │ ✗        │ ✓          │ ✗           │
│ Dashboard       │ ✗        │ ✗          │ ✓           │
│ API             │ ✗        │ ✗          │ ✓           │
│ Production Ready│ ✗        │ ✓          │ ✓           │
└─────────────────┴──────────┴────────────┴─────────────┘
```

---

Enjoy! 🎉
