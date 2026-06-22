# 📚 Faust Streaming — Hướng dẫn hoàn chỉnh

## Giới thiệu

**Faust** là thư viện xử lý stream phân tán mang các ý tưởng từ Kafka Streams sang Python. Bài tập này hướng dẫn:

1. ✅ **Cài đặt và thiết lập môi trường** (Docker + Kafka)
2. ✅ **Thực nghiệm Faust cơ bản** (app_base.py)
3. ✅ **Tính năng 1: Dead Letter Queue (DLQ) + Exponential Backoff Retry** (feature1_dlq.py)
4. ✅ **Tính năng 2: Distributed Real-time Metrics Dashboard** (feature2_metrics.py)

---

## 📁 Cấu trúc dự án

```
faust-midterm/
├── docker-compose.yml          # Kafka + Zookeeper
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container image
├── .dockerignore               # Docker build exclusions
├── setup.sh                    # Setup script
├── models.py                   # Data models chung (Order, OrderEvent)
├── app_base.py                 # Demo cơ bản 3 khái niệm chính
├── feature1_dlq.py             # Tính năng 1: DLQ + Retry
├── feature2_metrics.py         # Tính năng 2: Metrics Dashboard
├── producer.py                 # Test data producer
└── README.md                   # File này
```

---

## ⚡ Bước 1: Thiết lập môi trường

### 1.1 Yêu cầu hệ thống

- **Docker** & **Docker Compose**
- **Python 3.9+**
- **pip** (Python package manager)

### 1.2 Clone/Tạo dự án

```bash
mkdir faust-midterm && cd faust-midterm
# (Sao chép các file từ repo hoặc đã chuẩn bị)
```

### 1.3 Cài đặt Python dependencies

```bash
# Cách 1: Dùng script
chmod +x setup.sh
./setup.sh

# Cách 2: Thủ công
pip install -r requirements.txt
```

### 1.4 Khởi động Kafka

```bash
# Chạy Kafka + Zookeeper trong background
docker-compose up -d

# Kiểm tra containers
docker ps
# Nên thấy: faust-kafka và faust-zookeeper

# Xem logs
docker-compose logs -f kafka

# Dừng khi cần
docker-compose down
```

**⚠️ Lưu ý quan trọng:** Dùng **`faust-streaming`**, KHÔNG phải `faust` gốc (đã bị bỏ bảo trì).
Import vẫn là `import faust` như thường.

---

## 📚 Bước 2: Hiểu 3 khái niệm cốt lõi của Faust

### 2.1 Topic

- Là kênh truyền dữ liệu, tương ứng với Kafka topic
- Mỗi message chứa một object (ở đây là `Order`)
- Faust tự động serialize/deserialize JSON

```python
orders_topic = app.topic('orders', value_type=Order)
```

### 2.2 Agent

- Là coroutine async chạy mãi, đọc từng message từ stream
- Được Kafka chia sẻ: nếu chạy 2 workers, mỗi cái xử lý một phần partition
- Có thể chạy nhiều agent trên cùng topic hoặc topic khác

```python
@app.agent(orders_topic)
async def process_orders(stream):
    async for order in stream:
        # Xử lý logic
        pass
```

### 2.3 Table (Distributed State)

- Bảng phân tán, lưu state chung giữa các worker
- Tất cả workers đều có quyền đọc/ghi
- Faust tự động sync qua Kafka changelog topic
- Dữ liệu luôn nhất quán, không cần synchronize thủ công

```python
order_count_by_user = app.Table('order_count_by_user', default=int)
order_count_by_user['user_123'] += 1  # Tất cả workers thấy được
```

---

## 🧪 Bước 3: Chạy App cơ bản (app_base.py)

Minh họa 3 khái niệm trên với hệ thống đơn giản: đếm số đơn hàng theo user và tính tổng doanh thu.

### 3.1 Terminal 1: Chạy Worker thứ nhất

```bash
faust -A app_base worker -l info
```

Output:
```
[2024-01-15 10:30:00] INFO: faust: Starting worker...
[2024-01-15 10:30:02] INFO: app.agent: Topic 'orders' partitions ready
```

### 3.2 Terminal 2: Chạy Worker thứ hai (để demo phân tán)

```bash
faust -A app_base worker -l info --web-port 6067
```

**Lợi ích chạy 2 workers:**
- Kafka chia partitions cho mỗi worker
- Tất cả workers chia sẻ Faust Tables (dữ liệu luôn nhất quán)
- Độ chịu lỗi: nếu worker 1 crash, worker 2 vẫn xử lý tiếp

### 3.3 Terminal 3: Gửi test data

```bash
python producer.py -n 15 -i 0.8
```

Output:
```
[  1/15] 📦 ORD-A1B2C3D4 | Laptop x2 = $2198.00
[  2/15] 📦 ORD-B5C6D7E8 | Phone x1 = $899.00
...
✅ Đã gửi 15 orders vào topic 'orders'
```

### 3.4 Quan sát kết quả

Trên Terminal 1 và 2, sẽ thấy:

```
[10:30:45] ✅ [ORD-A1B2C3D4] Laptop x2 = $2198.00 | User user_2 — Tổng đơn: 1
[10:30:46] ✅ [ORD-B5C6D7E8] Phone x1 = $899.00 | User user_4 — Tổng đơn: 2
...
[10:31:00] ═══ TÓNG HỢP (App Base) ═══
  Người dùng: 5
  Tổng đơn: 15
  Tổng doanh thu: $15234.50
  Top sản phẩm:
    - Laptop: 5 đơn, $10990.00
    - Phone: 4 đơn, $3596.00
    - Tablet: 3 đơn, $2298.50
```

---

## 🛡️ Bước 4: Tính năng 1 — Dead Letter Queue + Exponential Backoff Retry

### 4.1 Khái niệm

**Dead Letter Queue (DLQ)** là một mẫu xử lý lỗi trong stream processing:

1. Message nhận từ topic chính
2. Nếu xử lý thất bại → retry với **exponential backoff** (chờ 2^n giây)
3. Nếu vượt MAX_RETRIES (3 lần) → đẩy vào **DLQ** để xử lý thủ công
4. Tất cả workers chia sẻ trạng thái retry qua Faust Table

Luồng:

```
orders ──────►  main_processor  ──(fail)──►  orders_retry  ──►  retry_processor
                      │                                               │
                      │                                          (xử lý lại)
                      │                                               │
                      ◄──────────────────────────────(fail lần 3)─────┘
                      │
                      └──►  orders_dlq  ──►  dlq_monitor  (log, alert)
```

### 4.2 Tính phân tán

- `dlq_stats` Table lưu thống kê: total, success, retry_sent, dlq
- Tất cả workers đọc/ghi cùng bảng
- Báo cáo định kỳ (mỗi 20s) hiển thị chính xác từ tất cả workers

### 4.3 Chạy thử

**Terminal 1:**
```bash
faust -A feature1_dlq worker -l info
```

**Terminal 2:**
```bash
faust -A feature1_dlq worker -l info --web-port 6067
```

**Terminal 3:** Gửi 20 đơn, 40% fail
```bash
python producer.py -n 20 -i 1.5 -f 0.4
```

### 4.4 Quan sát kết quả

Output ví dụ:

```
[10:35:20] ✅ OK    ORD-ABC123 — Laptop x1
[10:35:22] ⚠️  FAIL  FAIL-XYZ789 (lần 1/3): Sai định dạng order: FAIL-XYZ789
         → Retry sau 2s...
[10:35:24] 🔄 RETRY 1/3 thất bại cho FAIL-XYZ789. Thử lại sau 4s
[10:35:28] 🔄 RETRY 2/3 thất bại cho FAIL-XYZ789. Thử lại sau 8s
[10:35:36] ❌ DLQ   FAIL-XYZ789 hết lần retry

============================================================
  🚨 DLQ ALERT — 10:35:36
  Order ID    : FAIL-XYZ789
  User        : user_3
  Sản phẩm   : Phone x2
  Giá/đơn    : $899.00
  Lỗi cuối   : Sai định dạng order: FAIL-XYZ789
  Đã retry   : 3 lần
  Hành động  : Cần xử lý thủ công hoặc notify admin!
============================================================

[10:35:55] 📊 Báo cáo DLQ:
  Nhận tổng    : 20
  Thành công   : 12  (60.0%)
  Retry đã gửi : 7
  Vào DLQ      : 1
```

### 4.5 Cải tiến có thể làm

- Gửi email alert khi message vào DLQ
- Lưu DLQ vào database để admin review
- Thêm circuit breaker để tạm dừng khi lỗi quá nhiều
- Tự động retry từ DLQ sau khi service phục hồi

---

## 📊 Bước 5: Tính năng 2 — Distributed Real-time Metrics Dashboard

### 5.1 Khái niệm

Tính năng này thu thập metrics từ stream và expose qua web API + HTML dashboard:

- **Metrics Tables:**
  - `global_stats`: total_orders, total_revenue, avg_order_value
  - `orders_by_user`: đơn hàng theo user
  - `revenue_by_prod`: doanh thu theo sản phẩm
  - `throughput`: đơn/phút (20 phút gần nhất)

- **HTTP API:**
  - `/metrics/summary` — Tóm tắt
  - `/metrics/users` — Theo user
  - `/metrics/products` — Theo sản phẩm
  - `/metrics/throughput` — Throughput

- **HTML Dashboard:**
  - `/dashboard` — Interactive charts (Chart.js)
  - Auto-refresh mỗi 5 giây
  - 3 biểu đồ: doanh thu, đơn/user, throughput

### 5.2 Tính phân tán

- Mỗi worker xử lý một phần partitions từ `orders` topic
- Nhưng tất cả cập nhật **cùng Faust Tables** via Kafka changelog
- Faust tự động handle conflict resolution
- Web server (port 6066) access tất cả metrics tức thời

### 5.3 Chạy thử

**Terminal 1:**
```bash
faust -A feature2_metrics worker -l info
```

**Terminal 2:**
```bash
faust -A feature2_metrics worker -l info --web-port 6067
```

**Terminal 3:** Gửi 50 đơn liên tục
```bash
python producer.py -n 50 -i 0.5
```

### 5.4 Truy cập Dashboard

Mở trình duyệt:

```
http://localhost:6066/dashboard
```

**Sẽ thấy:**
- 5 card metrics (tổng đơn, doanh thu, avg, sản phẩm, user)
- 3 biểu đồ:
  - Doanh thu theo sản phẩm (doughnut)
  - Đơn hàng theo user (bar)
  - Throughput (line chart, 20 phút)
- Auto-refresh mỗi 5 giây

### 5.5 API JSON

```bash
# Tóm tắt
curl http://localhost:6066/metrics/summary
# {"total_orders": 50, "total_revenue": 45230.50, "avg_order_value": 904.61}

# Theo user
curl http://localhost:6066/metrics/users
# {"user_1": 10, "user_2": 8, "user_3": 12, ...}

# Theo sản phẩm
curl http://localhost:6066/metrics/products
# {"Laptop": {"orders": 8, "revenue": 15840.00}, ...}

# Throughput
curl http://localhost:6066/metrics/throughput
# {"10:35": 12, "10:36": 15, "10:37": 13, ...}
```

### 5.6 Console report

Mỗi 25 giây, các workers in report:

```
[10:40:00] ═══ METRICS REPORT ═══
  Tổng đơn  : 50
  Doanh thu : $45230.50
  Avg/đơn   : $904.61
  Top products:
    • Laptop: $15840.00
    • Phone: $12560.00
    • Tablet: $8430.50
```

---

## 🎯 So sánh 3 Ứng dụng

| Tính năng | app_base.py | feature1_dlq.py | feature2_metrics.py |
|-----------|------------|-------------|------|
| **Khái niệm** | Topic, Agent, Table | DLQ, Retry, Backoff | Metrics, API, Dashboard |
| **Topics** | 1 (orders) | 3 (orders, retry, dlq) | 1 (orders) |
| **Tables** | 3 (stats) | 4 (stats + DLQ counters) | 5 (detailed metrics) |
| **Agents** | 1 | 3 | 1 |
| **Concurrency** | 1 | 4 | 4 |
| **HTTP API** | Không | Không | Có (4 endpoints) |
| **Dashboard** | Không | Không | Có (http://localhost:6066) |
| **Error Handling** | Không | Có (DLQ) | Không |
| **Production Ready** | ❌ | ✅ | ✅ |

---

## 🐳 Bước 6: Chạy bằng Docker (Production)

### 6.1 Build image

```bash
docker build -t faust-app:latest .
```

### 6.2 Chạy container (đơn lẻ)

```bash
# Chạy app_base
docker run --rm --network host faust-app:latest \
    faust -A app_base worker -l info

# Chạy feature1_dlq
docker run --rm --network host faust-app:latest \
    faust -A feature1_dlq worker -l info
```

### 6.3 Chạy với docker-compose (đa worker)

Tạo file `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT

  faust_worker_1:
    build: .
    depends_on:
      - kafka
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    command: faust -A feature2_metrics worker -l info

  faust_worker_2:
    build: .
    depends_on:
      - kafka
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    command: faust -A feature2_metrics worker -l info --web-port 6067
    ports:
      - "6067:6067"

  faust_metrics:
    build: .
    depends_on:
      - kafka
    ports:
      - "6066:6066"
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    command: faust -A feature2_metrics worker -l info

  producer:
    build: .
    depends_on:
      - kafka
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:29092
    command: python producer.py -n 100 -i 0.3
```

Chạy:

```bash
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 📝 Tổng kết Kiến thức

### Khái niệm Faust

| Khái niệm | Mô tả | Ví dụ |
|----------|------|-------|
| **App** | Instance của ứng dụng Faust | `app = faust.App('name', broker='...')` |
| **Topic** | Kafka topic + serialization | `orders = app.topic('orders', value_type=Order)` |
| **Agent** | Async consumer xử lý stream | `@app.agent(topic) async def process(s): ...` |
| **Table** | Distributed state store | `stats = app.Table('stats', default=int)` |
| **View** | Read-only view của Table | `@app.view_changes(table)` |
| **Timer** | Callback chạy định kỳ | `@app.timer(10.0) async def tick(): ...` |

### Distributed Processing

- ✅ **Scaling**: Chạy nhiều workers, Kafka chia sẻ data
- ✅ **State Sharing**: Faust Tables sync tự động qua changelog
- ✅ **Fault Tolerance**: Nếu worker crash, partition được gán lại
- ✅ **Consistency**: No manual synchronization needed

### Best Practices

1. **Dùng async/await**: Không block event loop
2. **Batch processing**: `async for msg in stream` (Faust handles batching)
3. **Error handling**: Dùng DLQ cho message thất bại
4. **Monitoring**: Export metrics (Prometheus, CloudWatch, etc.)
5. **Partitioning**: Ensure even data distribution cho scalability

---

## 🆘 Troubleshooting

### Kafka không kết nối

```bash
# Kiểm tra containers
docker ps

# Xem logs Kafka
docker-compose logs kafka

# Restart
docker-compose restart
```

### Import error: `No module named 'faust'`

```bash
# Cài lại dependencies
pip install --upgrade -r requirements.txt

# Kiểm tra version
python -c "import faust; print(faust.__version__)"
# Should be 0.10.14
```

### Port 6066 đã dùng

Chỉ định port khác trong code hoặc dùng option:

```bash
faust -A feature2_metrics worker --web-port 6068
```

### Metrics không update

Kiểm tra:

```bash
# Xem Kafka topics
docker exec faust-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Xem message trong topic
docker exec faust-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic orders \
    --from-beginning \
    --max-messages 5
```

---

## 🎓 Bài tập mở rộng

### Bài 1: Thêm Windowing

Tính thống kê trên cửa sổ thời gian (ví dụ: 5 phút gần nhất):

```python
@app.agent(orders_topic)
async def windowed_processor(stream):
    async for event in stream.group_by(Order.product).take(
        timedelta(minutes=5), within=timedelta(minutes=6)
    ):
        # Process 5-minute window
        pass
```

### Bài 2: Thêm Join

Join 2 streams (orders + shipments):

```python
orders_stream = app.topic('orders')
shipments_stream = app.topic('shipments')

@app.agent(orders_stream)
async def join_processor(stream):
    shipments = shipments_stream.group_by('order_id')
    async for order in stream:
        shipment = await shipments.get(order.order_id)
        # Process joined record
        pass
```

### Bài 3: Persistence

Lưu DLQ message vào database:

```python
@app.agent(dlq_topic)
async def save_dlq_to_db(stream):
    async for order in stream:
        await db.dlq_orders.insert_one({
            'order_id': order.order_id,
            'error': order.error_message,
            'timestamp': datetime.now(),
        })
```

### Bài 4: Custom Serializer

Dùng Avro thay vì JSON:

```python
class Order(faust.Record, serializer='avro'):
    ...
```

---

## 📚 Tài liệu tham khảo

- **Faust Docs**: https://faust.readthedocs.io/
- **Kafka Streams**: https://kafka.apache.org/documentation/streams/
- **Confluent Kafka**: https://www.confluent.io/confluent-kafka/
- **Python Async**: https://docs.python.org/3/library/asyncio.html

---

## ✅ Checklist hoàn thành

- [ ] Cài đặt Python dependencies
- [ ] Khởi động Kafka qua docker-compose
- [ ] Chạy app_base.py với 2 workers
- [ ] Gửi test data với producer.py
- [ ] Quan sát output trên console
- [ ] Chạy feature1_dlq.py (DLQ) với 40% fail-rate
- [ ] Kiểm tra DLQ alerts
- [ ] Chạy feature2_metrics.py
- [ ] Truy cập dashboard (http://localhost:6066/dashboard)
- [ ] Test API endpoints
- [ ] Chạy multiple workers (2+) để verify distributed processing
- [ ] Build Docker image
- [ ] (Optional) Deploy bằng docker-compose.prod.yml

---

**Chúc bạn hoàn thành bài tập thành công!** 🚀
