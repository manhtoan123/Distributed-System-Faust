# Faust Midterm Project — Distributed Stream Processing

Dự án minh họa thư viện **Faust** (faust-streaming) — port các ý tưởng của Kafka Streams sang Python.

## 📁 Cấu trúc dự án
```
faust-midterm/
├── docker-compose.yml        # Kafka + Zookeeper
├── requirements.txt
├── models.py                 # Data model dùng chung (Order)
├── app_base.py               # Demo cơ bản: Topic / Agent / Table
├── feature1_dlq.py           # Tính năng 1: Dead Letter Queue + Retry
├── feature2_metrics.py       # Tính năng 2: Distributed Metrics Dashboard
└── producer.py                # Gửi test data vào Kafka
```

## ⚙️ Bước 1 — Cài đặt môi trường

> ⚠️ Dùng `faust-streaming` (KHÔNG phải `faust` gốc, đã bị bỏ bảo trì).
> Import trong code vẫn là `import faust` như thường.

```bash
pip install -r requirements.txt
```

Khởi động Kafka + Zookeeper cục bộ:
```bash
docker-compose up -d
docker ps   # Kiểm tra kafka và zookeeper đang chạy
```

## ▶️ Bước 2 — Demo cơ bản

```bash
# Terminal A
faust -A app_base worker -l info

# Terminal B (worker thứ 2 — thể hiện tính phân tán)
faust -A app_base worker -l info --web-port 6067

# Terminal C — gửi data
python producer.py -n 15 -i 0.8
```

## 🛡️ Bước 3 — Tính năng 1: Dead Letter Queue + Retry

**Ý tưởng phân tán:** dùng Faust `Table` để theo dõi trạng thái retry trên mọi worker.
Message thất bại được tự động retry với exponential backoff; sau khi hết số lần thử thì đẩy vào DLQ.

```
orders ──► main_processor ──(fail)──► retry_topic ──► retry_processor
              │                                            │
              │(max retry)                          (max retry)
              └──────────────────────────────────────────► │
                                                       dlq_topic
                                                            │
                                                       dlq_monitor
                                                      (alert/log)
```

```bash
# Terminal A (dừng app_base trước, rồi chạy)
faust -A feature1_dlq worker -l info

# Terminal B (worker 2 để thấy tính phân tán)
faust -A feature1_dlq worker -l info --web-port 6067

# Terminal C — gửi data với 40% fail để thấy retry/DLQ
python producer.py -n 20 -i 1.5 -f 0.4
```

## 📊 Bước 4 — Tính năng 2: Distributed Metrics Dashboard

**Ý tưởng phân tán:** nhiều Faust `Table` làm kho metrics chung — tất cả workers ghi vào cùng bảng
(qua Kafka changelog). Web server tích hợp sẵn của Faust expose API + dashboard HTML tự refresh.

```bash
# Terminal A
faust -A feature2_metrics worker -l info

# Terminal B (worker 2)
faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C — gửi data liên tục
python producer.py -n 50 -i 0.5
```

Mở trình duyệt:
- Dashboard: http://localhost:6066/dashboard
- API tổng quan: http://localhost:6066/metrics/summary
- API theo user: http://localhost:6066/metrics/users
- API theo sản phẩm: http://localhost:6066/metrics/products
- API throughput: http://localhost:6066/metrics/throughput

## 🧪 Dừng môi trường

```bash
docker-compose down
```

## Ghi chú khi báo cáo / nộp bài

- **Tính phân tán (distributed processing)** được thể hiện qua:
  - **Faust Table** (đồng bộ qua Kafka changelog topic) — mọi worker đọc/ghi cùng state dù chạy trên process/máy khác nhau.
  - **Partition tự động chia bởi Kafka** giữa các worker trong cùng consumer group — chạy thử với 2 worker (`--web-port 6067` ở worker thứ hai) để quan sát việc chia tải.
  - **Agent độc lập theo topic** (`main_processor`, `retry_processor`, `dlq_monitor`) — mỗi agent là một luồng xử lý phân tán riêng, giao tiếp với nhau qua Kafka topic trung gian (`orders_retry`, `orders_dlq`).
- Tính năng 1 (DLQ + Retry) minh họa khả năng chịu lỗi (fault tolerance) trong hệ phân tán.
- Tính năng 2 (Metrics Dashboard) minh họa việc tổng hợp state phân tán (aggregation) thành một view tập trung.
