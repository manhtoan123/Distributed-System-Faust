# 📖 Chi tiết 2 Tính năng

## Tính năng 1: Dead Letter Queue (DLQ) + Exponential Backoff Retry

### 1.1 Problem Statement

Trong xử lý stream, message không phải lúc nào cũng thành công:
- API payment bị timeout
- Database tạm thời down
- Validation error

**Vấn đề:** Cách xử lý nào khi message thất bại?

**Giải pháp:** DLQ + Retry Pattern

### 1.2 Architecture

```
orders (Kafka topic)
   ↓
main_processor (Agent)
   ├─ Thành công? → Update counter, xong
   └─ Thất bại?
       ├─ retry_count <= MAX_RETRIES?
       │  └─ YES: Gửi sang orders_retry + chờ exponential backoff
       │  └─ NO: Gửi sang orders_dlq (Dead Letter Queue)
       └─ (repeat cho orders_retry topic)

orders_retry (Kafka topic)
   ↓
retry_processor (Agent)
   ├─ Thành công? → Update counter
   └─ Thất bại? → (same logic lại)

orders_dlq (Kafka topic)
   ↓
dlq_monitor (Agent)
   ├─ Log alert
   ├─ Gửi email/Slack (thực tế)
   └─ Save vào database để admin xử lý thủ công
```

### 1.3 Exponential Backoff

**Ý tưởng:** Mỗi lần retry, chờ lâu hơn để service phục hồi

```python
delay = BACKOFF_BASE ^ retry_count  # 2^n

retry_count = 1: delay = 2^1 = 2 seconds
retry_count = 2: delay = 2^2 = 4 seconds
retry_count = 3: delay = 2^3 = 8 seconds
```

**Lợi ích:**
- Không quá tải service đang bị lỗi
- Cho time để service recover
- Giảm "thundering herd" effect

### 1.4 Distributed State Tracking

```python
dlq_stats = app.Table('dlq_stats', default=int)

# Tất cả workers cập nhật cùng bảng
dlq_stats['total'] += 1
dlq_stats['success'] += 1
dlq_stats['retry_sent'] += 1
dlq_stats['dlq'] += 1

# Faust tự động sync qua Kafka changelog topic
# → Dữ liệu luôn nhất quán, không cần locking
```

**Khi chạy 2+ workers:**
- Worker 1 và Worker 2 xử lý partition khác nhau
- Nhưng cả 2 đều cập nhật cùng Faust Table
- Faust Handle conflict resolution (last-write-wins)
- Tất cả workers thấy consistent view

### 1.5 Key Metrics

```
📊 DLQ Report:
  Nhận tổng    : 20 orders
  Thành công   : 12 (60%)
  Retry đã gửi : 7 (xung quanh)
  Vào DLQ      : 1 (admin xử lý)
  
Success Rate = 12 / 20 = 60%
```

### 1.6 Thực tế Production

```python
@app.agent(dlq_topic)
async def dlq_monitor(stream):
    async for order in stream:
        # 1. Lưu vào DLQ database
        await db.dlq_orders.insert_one({
            'order_id': order.order_id,
            'error': order.error_message,
            'retry_count': order.retry_count,
            'timestamp': datetime.now(),
        })
        
        # 2. Gửi alert
        await send_slack(
            f"DLQ Alert: {order.order_id} — {order.error_message}"
        )
        
        # 3. Gửi email admin
        await send_email(
            to='admin@company.com',
            subject=f'DLQ Order: {order.order_id}',
            body=f'...'
        )
```

### 1.7 Configuration Tuning

```python
MAX_RETRIES = 3           # Bao nhiêu lần thử
BACKOFF_BASE = 2          # Exponential base
BACKOFF_MAX = 60          # Max chờ (giây)
```

**Tính toán:**
- 3 retries × (2 + 4 + 8) = 14 seconds total
- Nếu MAX_RETRIES = 5: tổng cộng ~62 seconds

---

## Tính năng 2: Distributed Real-time Metrics Dashboard

### 2.1 Problem Statement

**Yêu cầu:** Monitor xử lý stream real-time
- Tổng số orders / doanh thu / avg
- Thống kê theo user / product
- Throughput (orders/phút)

**Thách thức:**
- Multiple workers xử lý song song
- Cần aggregated metrics từ tất cả workers
- Real-time update (không delay)
- Visual dashboard

### 2.2 Architecture

```
orders (Kafka topic, 3 partitions)
   ↓
Worker 1          Worker 2          Worker 3
(partition 0)     (partition 1)     (partition 2)
   │                  │                │
   └─ metrics_collector (Agent, concurrency=4)
                       │
                       ↓
              Faust Tables (distributed)
              ├─ global_stats
              ├─ orders_by_user
              ├─ revenue_by_prod
              ├─ orders_by_prod
              └─ throughput
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    HTTP API      Dashboard      Console Report
    /metrics/...   (Chart.js)    (mỗi 25s)
```

### 2.3 Faust Tables (Distributed)

```python
# Mỗi worker chạy concurrency=4, xử lý partitions
# Tất cả cập nhật cùng Faust Tables

global_stats = app.Table('m_global', default=float)
global_stats['total_orders'] += 1
global_stats['total_revenue'] += revenue

# Faust changelog topic: m_global-changelog
# Auto-replicate tất cả updates giữa workers
```

**Consistency Model:**
- Write: Synchronous (wait for Kafka ack)
- Read: Eventual consistent
- Conflict: Last-write-wins

### 2.4 HTTP API Endpoints

```
GET /metrics/summary
→ {
    "total_orders": 50,
    "total_revenue": 45230.50,
    "avg_order_value": 904.61,
    "timestamp": "2024-01-15T10:45:00"
  }

GET /metrics/users
→ {
    "user_1": 10,
    "user_2": 8,
    "user_3": 12,
    ...
  }

GET /metrics/products
→ {
    "Laptop": {"orders": 8, "revenue": 15840.00},
    "Phone": {"orders": 12, "revenue": 10788.00},
    ...
  }

GET /metrics/throughput
→ {
    "10:35": 12,
    "10:36": 15,
    "10:37": 13,
    ...
  }
```

### 2.5 Dashboard (HTML + Chart.js)

**Được lưu trữ tại:** `/dashboard` (route trong app)

**Features:**
- 5 metric cards (tổng, doanh thu, avg, products, users)
- 3 charts:
  1. Doanh thu theo sản phẩm (doughnut)
  2. Đơn hàng theo user (bar)
  3. Throughput (line, 20 phút gần nhất)
- Auto-refresh mỗi 5 giây
- Real-time update (fetch API)

**Stack:**
- Backend: Faust Web Server (built-in)
- Frontend: Plain HTML + Chart.js
- Communication: JSON API

### 2.6 Agent Implementation

```python
@app.agent(orders_topic, concurrency=4)
async def metrics_collector(stream):
    """
    Concurrency=4: Chạy 4 coroutine cùng lúc
    - Giúp xử lý nhanh hơn
    - Partition vẫn được Kafka chia cho worker
    - Faust handle ordering
    """
    async for order in stream:
        revenue = order.price * order.quantity
        minute = datetime.now().strftime('%H:%M')
        
        # Update distributed tables
        global_stats['total_orders'] += 1
        global_stats['total_revenue'] += revenue
        
        orders_by_user[order.user_id] += 1
        
        revenue_by_prod[order.product] += revenue
        orders_by_prod[order.product] += 1
        
        throughput[minute] += 1
        
        # Recalculate avg
        if global_stats['total_orders'] > 0:
            global_stats['avg_order_value'] = (
                global_stats['total_revenue'] 
                / global_stats['total_orders']
            )
```

### 2.7 Distributed Processing Example

**Scenario:** 30 orders, 3 partitions, 2 workers

```
Partition 0 (10 orders) → Worker 1
Partition 1 (10 orders) → Worker 1
Partition 2 (10 orders) → Worker 2

Xử lý song song → metrics_collector (Agent)
   ↓
Tất cả cập nhật cùng global_stats Table
   ↓
global_stats['total_orders'] = 30 (consistent)
global_stats['total_revenue'] = sum(all 30)
```

**Magic của Faust:**
- Không cần manual locking
- Không cần RPC call
- Tables tự sync via Kafka

### 2.8 Scaling

**Add more workers:**

```bash
# Worker 1
faust -A feature2_metrics worker -l info

# Worker 2
faust -A feature2_metrics worker -l info --web-port 6067

# Worker 3
faust -A feature2_metrics worker -l info --web-port 6068

# Worker 4
faust -A feature2_metrics worker -l info --web-port 6069
```

**Kafka auto-rebalances partitions**, tất cả workers vẫn share metrics

```
global_stats → Kafka changelog
   ↓
All 4 workers có consistent view
   ↓
Any worker's API serves correct metrics
```

### 2.9 Production Enhancements

```python
# 1. Prometheus export
@app.page('/metrics')
async def prometheus_metrics(web, request):
    return Response(text=f"""
# HELP faust_total_orders Total orders processed
# TYPE faust_total_orders counter
faust_total_orders {int(global_stats['total_orders'])}

# HELP faust_total_revenue Total revenue
# TYPE faust_total_revenue gauge
faust_total_revenue {float(global_stats['total_revenue'])}
    """, content_type='text/plain')

# 2. Alert thresholds
@app.timer(10.0)
async def check_metrics():
    if float(global_stats['total_orders']) > 1000:
        await send_alert("High volume detected!")

# 3. Metrics export to external DB
@app.timer(60.0)
async def export_metrics():
    await cloudwatch.put_metrics(
        Namespace='FaustApp',
        MetricData=[
            {
                'MetricName': 'TotalOrders',
                'Value': int(global_stats['total_orders']),
            },
            ...
        ]
    )
```

### 2.10 Dashboard Flow

```
Browser loads http://localhost:6066/dashboard
   ↓
Faust web server serves HTML
   ↓
JavaScript init (Chart.js)
   ↓
Fetch /metrics/summary, /metrics/users, /metrics/products, /metrics/throughput
   ↓
Parse JSON, update charts
   ↓
setInterval(load, 5000)
   ↓
Auto-refresh every 5 seconds
```

---

## So sánh lại

| Khía cạnh | Feature 1 (DLQ) | Feature 2 (Metrics) |
|-----------|-------------|----------|
| **Mục đích** | Handle failures | Monitor system |
| **Topics** | 3 (orders, retry, dlq) | 1 (orders) |
| **Tables** | 4 | 5 |
| **Agents** | 3 | 1 |
| **Error path** | Critical | Nice-to-have |
| **API** | Không | Có (4 endpoints) |
| **UI** | Không | Có (dashboard) |
| **Complexity** | Medium | High |
| **Production** | Essential | Recommended |

---

Hy vọng chi tiết này giúp hiểu sâu hơn! 🚀
