# Distributed Stream Processing with Apache Faust

**Môn: Ứng dụng Phân tán | Đề tài: Xây dựng hệ thống xử lý luồng dữ liệu phân tán sử dụng Faust**

---

## 1. Giới thiệu dự án

Dự án này minh họa một **hệ thống xử lý luồng dữ liệu phân tán (Distributed Stream Processing)** sử dụng **Apache Faust** — port của Kafka Streams sang Python. Dự án tập trung vào ba khái niệm cốt lõi:

- **Định danh & không gian tên:** Sử dụng Kafka topic để định danh và quản lý luồng dữ liệu
- **Truyền thông phân tán:** Tất cả worker giao tiếp thông qua Kafka broker trung tâm
- **Tính chịu lỗi (Fault Tolerance):** Sử dụng Dead Letter Queue (DLQ) và retry mechanism; Faust Table làm persistent state giữa các worker

Dự án bao gồm:
- **Baseline (app_base.py):** Demo 3 khái niệm cơ bản của Faust — Topic, Agent, Table
- **Feature 1 (feature1_dlq.py):** Dead Letter Queue + Exponential Backoff Retry
- **Feature 2 (feature2_metrics.py):** Real-time Distributed Metrics Dashboard

---

## 2. Kiến trúc hệ thống

### 2.1 Tổng quan

```
┌────────────────┐
│   Producer    │  (gửi Order vào 'orders' topic)
└────────┬───────┘
         │ kafka://localhost:9092
         ▼
    ┌─────────────────────────────────────────────────────┐
    │      Apache Kafka + Zookeeper (Docker)              │
    │  ┌──────────────────────────────────────────────┐   │
    │  │  Topics: orders, orders_retry, orders_dlq   │   │
    │  │  Partitions được chia tự động giữa workers  │   │
    │  └──────────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────────┘
         △          △          △
         │ consumer │ consumer │ consumer
    ┌────┴──┐  ┌────┴──┐  ┌────┴──┐
    │Worker1│  │Worker2│  │Worker3│  (các Faust App instance)
    │(Port  │  │(Port  │  │(Port  │   chạy cùng consumer group
    │ 6066) │  │ 6067) │  │ 6068) │   → tự chia partition
    └───────┘  └───────┘  └───────┘
```

### 2.2 Luồng xử lý dữ liệu

#### **Feature 1: Dead Letter Queue + Retry**

```
┌─────────────┐
│  orders     │ ────┐
│   topic     │     │
└─────────────┘     ▼
             main_processor
                  (agent)
                   │  ✅ success
                   │  → (Faust Table: dlq_stats['success']++)
                   │
                   ❌ fail (lần 1-3)
                   │ → retry_count++
                   │ → exponential backoff: await asyncio.sleep(2^n)
                   ▼
            ┌──────────────────┐
            │  orders_retry    │
            │     topic        │
            └──────────────────┘
                   │
                   ▼
            retry_processor
                 (agent)
                   │  ✅ success
                   │  → dlq_stats['success']++
                   │
                   ❌ fail (retry_count > MAX_RETRIES)
                   │
                   ▼
             ┌────────────────┐
             │  orders_dlq    │
             │     topic      │
             └────────────────┘
                   │
                   ▼
             dlq_monitor
               (agent)
          → Log alert
          → Thực tế: gửi email/Slack
```

Tính **phân tán**: 
- Khi chạy 2-3 worker cùng consumer group `faust-dlq`, Kafka tự động chia partition của `orders` topic
- Mỗi worker xử lý một phần message, nhưng **TẤT CẢ chia sẻ cùng** `dlq_stats` Faust Table (via Kafka changelog topic)
- Bảng `dlq_stats` được persistent → nếu 1 worker crash, worker khác vẫn có toàn bộ dữ liệu

#### **Feature 2: Distributed Metrics Dashboard**

```
┌──────────────┐
│  orders      │
│   topic      │
└──────┬───────┘
       │
       ▼
  metrics_collector
      (agent)
       │
       ├─► Faust Table 'global_stats'
       │   └─ {total_orders, total_revenue, avg_order_value}
       │
       ├─► Faust Table 'orders_by_user'
       │   └─ {user_id -> count}
       │
       ├─► Faust Table 'revenue_by_prod'
       │   └─ {product -> $revenue}
       │
       └─► Faust Table 'throughput'
           └─ {minute -> order_count}
           
    ┌─────────────────────────────────────┐
    │   Faust Web Server (Port 6066)      │
    │  /metrics/summary     (JSON API)    │
    │  /metrics/users       (JSON API)    │
    │  /metrics/products    (JSON API)    │
    │  /metrics/throughput  (JSON API)    │
    │  /dashboard           (HTML + JS)   │
    └─────────────────────────────────────┘
         │
         └─► Browser: auto-refresh 5 giây
             Chart.js visualization
```

Tính **phân tán**:
- Cả 3 worker chạy cùng `faust-metrics` consumer group
- Kafka chia partition `orders` topic → mỗi worker xử lý một phần message
- **Tất cả** ghi vào **cùng** Faust Tables (qua Kafka changelog) → metrics tập trung, chính xác
- Dashboard API đọc từ Faust Tables → luôn thấy dữ liệu nhất quán, realtime

---

## 3. Cấu trúc thư mục

```
Distributed-System-Faust/
├── docker-compose.yml        # Kafka + Zookeeper (1 broker, 1 ZK)
├── requirements.txt          # Thư viện Python
├── models.py                 # Order Faust Record
├── app_base.py               # Baseline: Topic, Agent, Table
├── feature1_dlq.py           # DLQ + Retry
├── feature2_metrics.py       # Metrics Dashboard
├── producer.py               # Gửi test data vào topic 'orders'
└── README.md                 # Tài liệu này
```

---

## 4. Yêu cầu môi trường

- **Python 3.8+**
- **Docker & Docker Compose** (để chạy Kafka + Zookeeper)
- **Cài đặt package:**
  ```bash
  pip install -r requirements.txt
  ```

---

## 5. Hướng dẫn chạy

### 5.1 Khởi động Kafka + Zookeeper

```bash
docker-compose up -d
docker ps   # Kiểm tra kafka và zookeeper đang chạy
```

Kafka sẽ chạy trên `localhost:9092`, Zookeeper trên `localhost:2181`.

### 5.2 Demo Baseline (app_base.py)

Mục đích: Minh họa **Topic, Agent, Table** của Faust.

```bash
# Terminal 1 — Worker 1
faust -A app_base worker -l info

# Terminal 2 — Worker 2 (chạy cùng consumer group, Kafka tự chia partition)
faust -A app_base worker -l info --web-port 6067

# Terminal 3 — Gửi test data
python producer.py -n 20 -i 1.0
```

**Quan sát:**
- Mỗi worker in message xử lý được
- Order count được lưu trong Faust Table `order_count_by_user` — tất cả worker chia sẻ
- Nếu dừng worker 1, worker 2 vẫn tiếp tục xử lý message từ partition của worker 1

---

### 5.3 Feature 1 Demo: DLQ + Retry (feature1_dlq.py)

Mục đích: Minh họa **Fault Tolerance** qua DLQ và retry mechanism với exponential backoff.

```bash
# Terminal 1 — Worker 1
faust -A feature1_dlq worker -l info

# Terminal 2 — Worker 2 (để thấy state sharing qua dlq_stats table)
faust -A feature1_dlq worker -l info --web-port 6067

# Terminal 3 — Gửi data với 40% failure rate
python producer.py -n 30 -i 1.0 -f 0.4
```

**Quan sát:**
- Message thất bại được retry với delay 2^n giây (exponential backoff)
- Sau MAX_RETRIES lần, message được đẩy vào DLQ
- `dlq_monitor` agent log alert khi message vào DLQ
- Bảng `dlq_stats` được chia sẻ → cả 2 worker cùng thấy `total`, `success`, `dlq` count

**Kiểm chứng chịu lỗi:**
- Đang chạy producer (đang gửi data), dừng Worker 1 bằng Ctrl+C
- Worker 2 sẽ tiếp tục xử lý những partition của Worker 1 → hệ thống không mất message

---

### 5.4 Feature 2 Demo: Metrics Dashboard (feature2_metrics.py)

Mục đích: Minh họa **aggregation** và **real-time visualization** của distributed metrics.

```bash
# Terminal 1 — Worker 1
faust -A feature2_metrics worker -l info

# Terminal 2 — Worker 2
faust -A feature2_metrics worker -l info --web-port 6067

# Terminal 3 — Worker 3
faust -A feature2_metrics worker -l info --web-port 6068

# Terminal 4 — Gửi data liên tục
python producer.py -n 100 -i 0.3
```

**Mở trình duyệt:**
- Dashboard: http://localhost:6066/dashboard
- API tổng quan: http://localhost:6066/metrics/summary
- API theo user: http://localhost:6066/metrics/users
- API theo sản phẩm: http://localhost:6066/metrics/products
- API throughput: http://localhost:6066/metrics/throughput

**Quan sát:**
- Dashboard auto-refresh 5 giây từ Faust Tables
- Mỗi worker nhận một phần message từ Kafka partition
- Nhưng tất cả ghi vào cùng Faust Tables → metrics luôn nhất quán, accurate
- Dừng 1 worker → dashboard vẫn hoạt động từ worker khác

---

### 5.5 Dừng môi trường

```bash
# Dừng Kafka + Zookeeper
docker-compose down

# Hoặc nếu muốn xóa volume (xóa toàn bộ dữ liệu Kafka)
docker-compose down -v
```

---

## 6. Producer options

```bash
python producer.py -h
# -n, --num        Số lượng order gửi (default: 20)
# -i, --interval   Khoảng thời gian giữa mỗi order (giây, default: 1.0)
# -f, --fail_rate  Tỉ lệ order fail khi xử lý (0.0-1.0, default: 0.0)
```

**Ví dụ:**
```bash
python producer.py -n 50 -i 0.5 -f 0.3
# Gửi 50 order, mỗi 0.5 giây, 30% sẽ fail
```

---

## 7. Khái niệm chính

### 7.1 **Faust Topic**
- Tương ứng với Kafka topic
- Producer gửi message vào topic
- Agent consume từ topic để xử lý

### 7.2 **Faust Agent**
- Coroutine async chạy liên tục (`async def`)
- Consume message từ topic stream
- Khi chạy nhiều worker: Kafka tự động chia partition → mỗi worker xử lý một phần
- Giao tiếp với nhau qua topic trung gian

### 7.3 **Faust Table (Distributed State)**
- Bảng key-value lưu trữ state phân tán
- Backed by Kafka changelog topic
- **Tất cả worker chia sẻ cùng table** — nếu worker A ghi key X, worker B đọc X sẽ thấy giá trị mới
- Persistent — nếu 1 worker crash, worker khác vẫn có toàn bộ dữ liệu

### 7.4 **Consumer Group**
- Khi chạy `faust -A app_name worker`, worker tham gia consumer group có tên là `app_name`
- Kafka tự động chia partition topic cho các worker trong group
- Nếu 1 worker crash → Kafka rebalance → partition được gán cho worker còn sót

### 7.5 **Exponential Backoff Retry**
- Thời gian chờ trước retry = `BACKOFF_BASE ^ retry_count`
- Giúp tránh quá tải dịch vụ khi thất bại tạm thời
- Sau MAX_RETRIES lần → đẩy vào DLQ

### 7.6 **Dead Letter Queue (DLQ)**
- Topic riêng lưu trữ message thất bại sau tất cả retry
- Thực tế: admin xem xét thủ công, hoặc trigger alert/notification

---

## 8. Ghi chú cho giáo viên — Cách kiểm chứng tính phân tán

### ✅ **Kiểm chứng Distributed Processing:**

1. **Chạy 2-3 worker cùng lúc** cho cùng app
   ```bash
   # Terminal A: faust -A feature1_dlq worker -l info
   # Terminal B: faust -A feature1_dlq worker -l info --web-port 6067
   # Terminal C: python producer.py -n 50 -i 0.5 -f 0.3
   ```

2. **Quan sát:**
   - Message được chia giữa worker A và B (đôi khi A in, đôi khi B in)
   - Table `dlq_stats` được chia sẻ → cả A và B đều cập nhật count chung

3. **Kiểm chứng Fault Tolerance:**
   - Khi producer vẫn chạy (Terminal C), dừng worker A (Ctrl+C)
   - Worker B sẽ nhận những partition của worker A → xử lý tiếp
   - **Không có message nào bị mất**

### ✅ **Kiểm chứng State Sharing (Faust Table):**

1. **Chạy feature2_metrics với 2-3 worker**
2. **Mở dashboard:** http://localhost:6066/dashboard
3. **Gửi data:** `python producer.py -n 100 -i 0.3`
4. **Quan sát:**
   - Dashboard thấy metrics tích lũy liên tục
   - Dừng 1 worker → dashboard vẫn update (từ worker khác)
   - Mở console của 2 worker → thấy cả 2 đều in, nhưng metrics luôn chính xác (không bị double-count)

---

## 9. Troubleshooting

### **Lỗi: "Port 9092 already in use"**
```bash
# Kiểm tra container nào chạy
docker ps

# Nếu Kafka cũ còn chạy
docker-compose down
docker-compose up -d
```

### **Lỗi: "faust command not found"**
```bash
pip install faust-streaming==0.10.14
```

### **Lỗi: "Worker không nhận message từ producer"**
- Kiểm tra docker-compose đã chạy: `docker ps`
- Kiểm tra kafka container log: `docker logs <kafka_container_id>`
- Kiểm tra producer gửi message thành công: thêm print() trong producer

### **Lỗi: "Faust Table không sync giữa 2 worker"**
- Cần chạy 2 worker với **cùng app name** (e.g., cả 2 `faust -A feature1_dlq worker`)
- Kiểm tra Kafka broker đang chạy
- Table changelog topic sẽ được tạo tự động (có tên `<app_name>-<table_name>-changelog`)

---

## 10. Tài liệu tham khảo

- **Faust Documentation:** https://faust.readthedocs.io/
- **Kafka Concepts:** https://kafka.apache.org/documentation/#intro_concepts
- **Docker Compose:** https://docs.docker.com/compose/
- **Referece Project:** https://github.com/shikai469/pupdb-distributed

---

## 11. Nhân viên dự án

| Sinh viên | Vai trò |
|-----------|--------|
| (Họ tên) | (Vai trò) |

---

**Ngày nộp:** [Ngày tháng năm]  
**Lớp:** [Lớp học]  
**Môn học:** Ứng dụng Phân tán
