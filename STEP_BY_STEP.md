# 🎬 Step-by-Step Execution Guide

Hướng dẫn chạy từng bước, screenshot/output expected ở mỗi bước.

---

## 📍 Bước 1: Chuẩn bị Môi trường (10 phút)

### 1.1 Kiểm tra Python & Docker

```bash
python --version
# Output: Python 3.9+ (tối thiểu 3.9)

docker --version
# Output: Docker 20.10+

docker-compose --version
# Output: Docker Compose 1.29+
```

❌ Nếu báo lỗi → cài Docker Desktop / Python từ python.org

### 1.2 Clone Repository

```bash
cd ~/projects  # hoặc thư mục nào bạn muốn
mkdir faust-midterm
cd faust-midterm

# Copy tất cả file từ repo/attachment vào thư mục này
# (hoặc git clone nếu có)
```

### 1.3 Cài Python Dependencies

```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed faust-streaming-0.10.14 kafka-python-2.0.2 aiohttp-3.9.5 click-8.1.7
```

### 1.4 Khởi động Kafka

```bash
docker-compose up -d
```

Expected output:
```
Creating faust-zookeeper ... done
Creating faust-kafka ... done
```

Verify:
```bash
docker ps
```

Expected:
```
CONTAINER ID   IMAGE                                    PORTS
xxx            confluentinc/cp-kafka:7.5.0              0.0.0.0:9092->9092/tcp
yyy            confluentinc/cp-zookeeper:7.5.0         0.0.0.0:2181->2181/tcp
```

### 1.5 Test Kafka Connection

```bash
python -c "
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers='localhost:9092')
print('✅ Kafka connection OK')
producer.close()
"
```

Expected:
```
✅ Kafka connection OK
```

---

## 🎯 Bước 2: Chạy App Cơ bản (Demo Topic, Agent, Table)

### Mục đích
- Hiểu 3 khái niệm cốt lõi của Faust: Topic, Agent, Table
- Thấy cách 2 workers chia sẻ distributed state

### 2.1 Terminal 1: Khởi động Worker 1

```bash
faust -A app_base worker -l info
```

Chờ khoảng 2-3 giây, bạn sẽ thấy:

```
[2024-01-15 10:30:00,123] INFO: faust: Starting worker
[2024-01-15 10:30:00,456] INFO: faust: Worker ready (pid=12345)
[2024-01-15 10:30:01,000] INFO: app.agent: Topic 'orders' partitions ready
```

⏸️ Để Terminal 1 này chạy

### 2.2 Terminal 2: Khởi động Worker 2 (2nd Worker)

**Mở tab/terminal mới:**

```bash
faust -A app_base worker -l info --web-port 6067
```

Expected:
```
[2024-01-15 10:30:05,123] INFO: faust: Starting worker
[2024-01-15 10:30:05,456] INFO: faust: Worker ready (pid=67890)
```

⏸️ Để Terminal 2 này chạy (song song với Terminal 1)

### 2.3 Terminal 3: Gửi Test Data

**Mở tab/terminal mới (lần 3):**

```bash
python producer.py -n 15 -i 0.8
```

Expected output:
```
📤 Gửi 15 đơn hàng
   Interval: 0.8s | Fail rate: 0.0%

[  1/15] 📦 ORD-A1B2C3D4 | Laptop x2 = $2198.00
[  2/15] 📦 ORD-B5C6D7E8 | Phone x1 = $899.00
[  3/15] 📦 ORD-C7D8E9F0 | Tablet x3 = $1497.00
...
[15/15] 📦 ORD-K9L0M1N2 | Watch x1 = $299.00

✅ Đã gửi 15 orders vào topic 'orders'
```

### 2.4 Quan sát Terminal 1 & 2

Trên **Terminal 1** (nếu nó xử lý partition 0):

```
[10:30:15] ✅ [ORD-A1B2C3D4] Laptop x2 = $2198.00 | User user_2 — Tổng đơn: 1
[10:30:16] ✅ [ORD-C7D8E9F0] Tablet x3 = $1497.00 | User user_4 — Tổng đơn: 2
[10:30:17] ✅ [ORD-E9F0A1B2] Phone x1 = $899.00 | User user_1 — Tổng đơn: 3
```

Trên **Terminal 2** (nếu nó xử lý partition 1 & 2):

```
[10:30:15] ✅ [ORD-B5C6D7E8] Phone x1 = $899.00 | User user_3 — Tổng đơn: 4
[10:30:16] ✅ [ORD-D8E9F0A1] Watch x2 = $598.00 | User user_5 — Tổng đơn: 5
[10:30:17] ✅ [ORD-F0A1B2C3] Keyboard x1 = $149.00 | User user_2 — Tổng đơn: 6
```

**Quan sát quan trọng:** "Tổng đơn" tăng liên tục (1, 2, 3, 4, 5, 6, ..., 15) — 
cho thấy cả 2 workers chia sẻ cùng Faust Table!

### 2.5 Báo cáo Periodic (mỗi 15 giây)

Khoảng 15 giây sau, bạn sẽ thấy:

```
[10:30:30] ═══ TÓNG HỢP (App Base) ═══
  Người dùng: 5
  Tổng đơn: 15
  Tổng doanh thu: $15234.50
  Top sản phẩm:
    - Laptop: 5 đơn, $10990.00
    - Phone: 4 đơn, $3596.00
    - Tablet: 3 đơn, $2298.50
```

### 2.6 Dừng Demo Cơ bản

```bash
# Terminal 1: Ctrl+C
# Terminal 2: Ctrl+C
```

---

## 🔁 Bước 3: Chạy Feature 1 — DLQ + Retry

### Mục đích
- Hiểu DLQ pattern: failure handling, exponential backoff, distributed error tracking
- Thấy message retry logic

### 3.1 Terminal 1: Khởi động Worker 1

```bash
faust -A feature1_dlq worker -l info
```

### 3.2 Terminal 2: Khởi động Worker 2

```bash
faust -A feature1_dlq worker -l info --web-port 6067
```

### 3.3 Terminal 3: Gửi Test Data (40% fail)

```bash
python producer.py -n 20 -i 1.5 -f 0.4
```

Expected output từ producer:
```
📤 Gửi 20 đơn hàng
   Interval: 1.5s | Fail rate: 40.0%

[  1/20] 📦 ORD-A1B2C3D4 | Laptop x2 = $2198.00
[  2/20] 💀 FAIL-X5Y6Z7W8 | Phone x1 = $899.00      ← Thất bại (sẽ retry)
[  3/20] 📦 ORD-B5C6D7E8 | Tablet x3 = $1497.00
...
```

### 3.4 Quan sát Retry Logic (Terminal 1)

```
[10:35:20] ✅ OK    ORD-A1B2C3D4 — Laptop x2

[10:35:22] ⚠️  FAIL  FAIL-X5Y6Z7W8 (lần 1/3): Sai định dạng order: FAIL-X5Y6Z7W8
         → Retry sau 2s...

[10:35:24] 🔄 RETRY 1/3 thất bại cho FAIL-X5Y6Z7W8. Thử lại sau 4s

[10:35:28] 🔄 RETRY 2/3 thất bại cho FAIL-X5Y6Z7W8. Thử lại sau 8s

[10:35:36] ❌ DLQ   FAIL-X5Y6Z7W8 — chuyển vào DLQ
```

**Backoff timing:**
- Retry 1: chờ 2^1 = 2 giây
- Retry 2: chờ 2^2 = 4 giây  
- Retry 3: chờ 2^3 = 8 giây

### 3.5 DLQ Alert (Terminal 1)

Sau khi message hết lần retry:

```
============================================================
  🚨 DLQ ALERT — 10:35:36
  Order ID    : FAIL-X5Y6Z7W8
  User        : user_3
  Sản phẩm   : Phone x2
  Giá/đơn    : $899.00
  Lỗi cuối   : Sai định dạng order: FAIL-X5Y6Z7W8
  Đã retry   : 3 lần
  Hành động  : Cần xử lý thủ công hoặc notify admin!
============================================================
```

### 3.6 DLQ Report (mỗi 20 giây)

```
[10:35:55] 📊 Báo cáo DLQ:
  Nhận tổng    : 20
  Thành công   : 12  (60.0%)
  Retry đã gửi : 7
  Vào DLQ      : 1
```

**Giải thích:**
- 20 messages tổng cộng
- 12 thành công
- 7 được send lại (một số thành công sau retry)
- 1 vào DLQ (max retries)

### 3.7 Dừng Feature 1

```bash
# Terminal 1, 2: Ctrl+C
```

---

## 📊 Bước 4: Chạy Feature 2 — Distributed Metrics Dashboard

### Mục đích
- Thấy distributed metrics gathering từ multiple workers
- Access real-time dashboard + API

### 4.1 Terminal 1: Khởi động Worker 1

```bash
faust -A feature2_metrics worker -l info
```

### 4.2 Terminal 2: Khởi động Worker 2

```bash
faust -A feature2_metrics worker -l info --web-port 6067
```

### 4.3 Terminal 3: Gửi Test Data (50 orders)

```bash
python producer.py -n 50 -i 0.5
```

### 4.4 Mở Dashboard trong Browser

**URL:** `http://localhost:6066/dashboard`

**Sẽ thấy:**

1. **Metric Cards (top):**
   - 📦 Total Orders: 50
   - 💰 Total Revenue: $45,230.50
   - 📈 Avg per Order: $904.61
   - 🛍️ Unique Products: 7
   - 👥 Unique Users: 5

2. **Charts (dưới):**
   - **Left:** Doughnut chart — Revenue by Product
     - Laptop: 30% (màu xanh)
     - Phone: 25% (màu xanh lá)
     - Tablet: 20% (màu cam)
     - etc.
   
   - **Right:** Bar chart — Orders by User
     - user_1: 12 orders
     - user_2: 8 orders
     - user_3: 15 orders
     - etc.
   
   - **Bottom:** Line chart — Throughput (20 phút)
     - X-axis: thời gian (HH:MM)
     - Y-axis: đơn/phút
     - Trend line tăng khi producer gửi

3. **Status:** "🟢 Live — 10:45:30" (tự refresh mỗi 5s)

### 4.5 Test API Endpoints

**Terminal 4 (hoặc curl bất kỳ):**

```bash
# API 1: Summary
curl http://localhost:6066/metrics/summary | python -m json.tool
```

Output:
```json
{
    "total_orders": 50,
    "total_revenue": 45230.50,
    "avg_order_value": 904.61,
    "timestamp": "2024-01-15T10:45:30.123456"
}
```

```bash
# API 2: Users
curl http://localhost:6066/metrics/users | python -m json.tool
```

Output:
```json
{
    "user_1": 12,
    "user_2": 8,
    "user_3": 15,
    "user_4": 10,
    "user_5": 5
}
```

```bash
# API 3: Products
curl http://localhost:6066/metrics/products | python -m json.tool
```

Output:
```json
{
    "Laptop": {
        "orders": 8,
        "revenue": 15840.00
    },
    "Phone": {
        "orders": 12,
        "revenue": 10788.00
    },
    ...
}
```

```bash
# API 4: Throughput
curl http://localhost:6066/metrics/throughput | python -m json.tool
```

Output:
```json
{
    "10:40": 8,
    "10:41": 12,
    "10:42": 15,
    "10:43": 10,
    "10:44": 5
}
```

### 4.6 Console Report (mỗi 25 giây)

```
[10:46:15] ═══ METRICS REPORT ═══
  Tổng đơn  : 50
  Doanh thu : $45230.50
  Avg/đơn   : $904.61
  Top products:
    • Laptop: $15840.00
    • Phone: $10788.00
    • Tablet: $8564.00
```

### 4.7 Verify Distributed Processing

**Terminal 1 output sample:**
```
[10:45:22] [METRICS] ORD-ABC123 | Laptop x2 = $1798.00 | Tổng đơn: 23
```

**Terminal 2 output sample:**
```
[10:45:23] [METRICS] ORD-XYZ789 | Phone x1 = $899.00 | Tổng đơn: 24
```

**Quan sát:** Tổng đơn tăng liên tục từ 23 → 24 → 25 → ... (cả 2 workers share metric)

### 4.8 Dừng Feature 2

```bash
# Terminal 1, 2: Ctrl+C
```

---

## 📋 Bước 5: Multi-Worker Demo (Optional Advanced)

Chạy **3+ workers** để thấy Kafka auto-rebalance partitions

### 5.1 Khởi động 3 Workers

```bash
# Terminal 1
faust -A feature2_metrics worker -l info

# Terminal 2
faust -A feature2_metrics worker -l info --web-port 6067

# Terminal 3
faust -A feature2_metrics worker -l info --web-port 6068
```

### 5.2 Gửi Data

```bash
# Terminal 4
python producer.py -n 100 -i 0.3
```

### 5.3 Quan sát Rebalancing

Lúc khởi động worker mới, bạn sẽ thấy:

```
[10:50:00] INFO: ...Assignment change...
[10:50:01] INFO: Worker rebalanced
[10:50:02] INFO: Starting agent...
```

Tất cả 3 workers sẽ get một phần partitions, xử lý song song.

Metrics dashboard vẫn consistent!

---

## ✅ Checklist Hoàn thành

- [ ] Bước 1: Môi trường chuẩn bị
  - [ ] Python + Docker cài
  - [ ] Dependencies cài
  - [ ] Kafka chạy
  - [ ] Test connection OK

- [ ] Bước 2: App cơ bản
  - [ ] 2 workers khởi động
  - [ ] Producer gửi data
  - [ ] Thấy distributed state

- [ ] Bước 3: DLQ
  - [ ] 2 workers khởi động
  - [ ] Producer gửi 40% fail
  - [ ] Thấy retry logic
  - [ ] Thấy DLQ alert

- [ ] Bước 4: Metrics
  - [ ] 2 workers khởi động
  - [ ] Producer gửi data
  - [ ] Dashboard load OK
  - [ ] API endpoints work
  - [ ] Charts update real-time

- [ ] Bước 5: (Optional) Multi-worker
  - [ ] 3+ workers run
  - [ ] Metrics consistent
  - [ ] Rebalancing verify

---

**Xong! You're ready to submit!** 🚀

