# 🎬 Hướng Dẫn Demo Chi Tiết (Tiếng Việt)

## 📍 Bước Chuẩn Bị: Clone Repository & Setup

### 1.1 Clone Repository từ GitHub

```bash
# Đi đến thư mục bạn muốn lưu project
cd ~/Documents
# hoặc cd C:\Users\YourUsername\Documents

# Clone repository
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust
```

**Expected output:**
```
Cloning into 'Distributed-System-Faust'...
remote: Enumerating objects...
Unpacking objects: 100% (50/50), done.
```

### 1.2 Kiểm tra thư mục

```bash
ls -la
# hoặc Windows: dir
```

**Nên thấy các file sau:**
```
.git/
.gitignore
.dockerignore
Dockerfile
docker-compose.yml
requirements.txt
models.py
app_base.py
feature1_dlq.py
feature2_metrics.py
producer.py
setup.sh
test_setup.sh
README.md
QUICK_START.md
STEP_BY_STEP.md
... (nhiều file .md khác)
```

### 1.3 Cài Python Dependencies

```bash
# Cài các thư viện cần thiết
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed faust-streaming-0.10.14 kafka-python-2.0.2 
aiohttp-3.9.5 click-8.1.7
```

### 1.4 Khởi động Kafka

```bash
# Chạy Kafka + Zookeeper trong Docker
docker-compose up -d
```

**Verify:**
```bash
docker ps
```

**Nên thấy:**
```
CONTAINER ID   IMAGE                              STATUS      PORTS
xxxxx          confluentinc/cp-kafka:7.5.0       Up 2 sec    0.0.0.0:9092->9092/tcp
yyyyy          confluentinc/cp-zookeeper:7.5.0   Up 3 sec    0.0.0.0:2181->2181/tcp
```

✅ **Nếu OK:** Tiếp tục bước tiếp theo

❌ **Nếu lỗi:** Xem [Troubleshooting](#troubleshooting)

---

## 🎯 DEMO 1: App Cơ Bản (15 phút)

Thể hiện: **Topics, Agents, Distributed Tables**

### Bước 1: Mở 3 Terminal/Tab

**Terminal A, B, C** — mở 3 cửa sổ command prompt/terminal

### Bước 2: Terminal A — Worker 1

```bash
cd Distributed-System-Faust
python -m faust -A app_base worker -l info
```

**Chờ khoảng 3-5 giây, bạn sẽ thấy:**

```
[2024-01-15 10:30:00,123] INFO: faust: Starting worker
[2024-01-15 10:30:01,234] INFO: faust: Worker ready (pid=12345)
[2024-01-15 10:30:02,345] INFO: app.agent: Topic 'orders' partitions ready
```

⏸️ **Để Terminal A chạy, đừng đóng!**

### Bước 3: Terminal B — Worker 2 (để demo distributed)

**Mở tab/terminal mới:**

```bash
cd Distributed-System-Faust
python -m faust -A app_base worker -l info --web-port 6067
```

**Chờ 2-3 giây, sẽ thấy:**

```
[2024-01-15 10:30:05,456] INFO: faust: Starting worker
[2024-01-15 10:30:06,567] INFO: faust: Worker ready (pid=67890)
```

⏸️ **Để Terminal B chạy!**

### Bước 4: Terminal C — Gửi Test Data

**Mở tab/terminal thứ 3:**

```bash
cd Distributed-System-Faust
python producer.py -n 15 -i 0.8
```

**Output:**
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

### Bước 5: Quan Sát Terminal A & B

**Bạn sẽ thấy từng order được xử lý:**

#### Terminal A Output:
```
[10:30:15] ✅ [ORD-A1B2C3D4] Laptop x2 = $2198.00 | User user_2 — Tổng đơn: 1
[10:30:16] ✅ [ORD-C7D8E9F0] Tablet x3 = $1497.00 | User user_4 — Tổng đơn: 2
[10:30:17] ✅ [ORD-E9F0A1B2] Phone x1 = $899.00 | User user_1 — Tổng đơn: 3
```

#### Terminal B Output:
```
[10:30:15] ✅ [ORD-B5C6D7E8] Phone x1 = $899.00 | User user_3 — Tổng đơn: 4
[10:30:16] ✅ [ORD-D8E9F0A1] Watch x2 = $598.00 | User user_5 — Tổng đơn: 5
[10:30:17] ✅ [ORD-F0A1B2C3] Keyboard x1 = $149.00 | User user_2 — Tổng đơn: 6
```

### 🔑 **Quan Sát Quan Trọng:**

Nhìn cột **"Tổng đơn"**: `1 → 2 → 3 → 4 → 5 → 6 → ... → 15`

**Điều này chứng minh:**
- ✅ Worker A xử lý một số order
- ✅ Worker B xử lý những order khác
- ✅ **Cả 2 workers CHIA SẼ cùng một Faust Table**
- ✅ Dữ liệu luôn nhất quán (không cần locking!)

### Bước 6: Báo Cáo Periodic (chờ ~15 giây)

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

### Bước 7: Dừng Demo 1

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
# Terminal C: (đã xong)
```

---

## 🛡️ DEMO 2: Feature 1 — DLQ + Retry (20 phút)

Thể hiện: **Exponential Backoff, Distributed Error Tracking, DLQ Alert**

### Bước 1: Mở 3 Terminal Mới

### Bước 2: Terminal A — Worker 1

```bash
cd Distributed-System-Faust
python -m faust -A feature1_dlq worker -l info
```

### Bước 3: Terminal B — Worker 2

```bash
cd Distributed-System-Faust
python -m faust -A feature1_dlq worker -l info --web-port 6067
```

### Bước 4: Terminal C — Gửi Data (40% fail)

```bash
cd Distributed-System-Faust
python producer.py -n 20 -i 1.5 -f 0.4
```

**Output dari producer:**
```
📤 Gửi 20 đơn hàng
   Interval: 1.5s | Fail rate: 40.0%

[  1/20] 📦 ORD-A1B2C3D4 | Laptop x2 = $2198.00
[  2/20] 💀 FAIL-X5Y6Z7W8 | Phone x1 = $899.00    ← LỖI (40% xác suất)
[  3/20] 📦 ORD-B5C6D7E8 | Tablet x3 = $1497.00
[  4/20] 💀 FAIL-Y6Z7W8V9 | Watch x2 = $598.00    ← LỖI
...
```

### Bước 5: Quan Sát Retry Logic (Terminal A & B)

**Bạn sẽ thấy các order thất bại RETRY tự động:**

```
[10:35:20] ✅ OK    ORD-A1B2C3D4 — Laptop x2
           ✅ OK    ORD-B5C6D7E8 — Tablet x3

[10:35:22] ⚠️  FAIL  FAIL-X5Y6Z7W8 (lần 1/3): Sai định dạng order: FAIL-X5Y6Z7W8
           → Retry sau 2s...

[10:35:24] 🔄 RETRY 1/3 thất bại cho FAIL-X5Y6Z7W8. Thử lại sau 4s

[10:35:28] 🔄 RETRY 2/3 thất bại cho FAIL-X5Y6Z7W8. Thử lại sau 8s

[10:35:36] ❌ DLQ   FAIL-X5Y6Z7W8 — chuyển vào DLQ
```

### 🔑 **Exponential Backoff Timing:**

| Lần | Chờ | Giây |
|-----|-----|------|
| Retry 1 | 2^1 = | 2s |
| Retry 2 | 2^2 = | 4s |
| Retry 3 | 2^3 = | 8s |
| Tiếp theo | → DLQ | Alert |

### Bước 6: DLQ Alert (sau mỗi order fail 3 lần)

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

### Bước 7: DLQ Report (mỗi 20 giây)

```
[10:35:55] 📊 Báo cáo DLQ:
  Nhận tổng    : 20
  Thành công   : 12  (60.0%)
  Retry đã gửi : 7
  Vào DLQ      : 1
```

**Giải thích:**
- Tổng 20 messages
- 12 thành công (60%)
- 7 được retry (một số thành công sau retry)
- 1 vào DLQ (thất bại hết cơ hội)

### Bước 8: Dừng Demo 2

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

## 📊 DEMO 3: Feature 2 — Metrics Dashboard (25 phút)

Thể hiện: **Real-time Metrics, HTTP API, Interactive Dashboard**

### Bước 1: Mở 3 Terminal Mới

### Bước 2: Terminal A — Worker 1

```bash
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info
```

### Bước 3: Terminal B — Worker 2

```bash
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info --web-port 6067
```

### Bước 4: Terminal C — Gửi Data (liên tục)

```bash
cd Distributed-System-Faust
python producer.py -n 50 -i 0.5
```

### Bước 5: Mở Browser & Truy cập Dashboard

**URL:** `http://localhost:6066/dashboard`

### 🎨 **Dashboard sẽ hiển thị:**

#### **5 Metric Cards (top):**
```
📦 Total Orders          💰 Total Revenue        📈 Avg per Order
      50                      $45,230.50               $904.61

🛍️ Unique Products       👥 Unique Users
        7                          5
```

#### **3 Charts (dưới):**

**1. Revenue by Product (Doughnut - tròn)**
```
    ┌─ Laptop: 30% (xanh)
    ├─ Phone: 25% (xanh lá)
    ├─ Tablet: 20% (cam)
    ├─ Watch: 15% (tím)
    └─ Others: 10%
```

**2. Orders by User (Bar - cột)**
```
    user_1: ████████████ (12 orders)
    user_2: ████████ (8 orders)
    user_3: ███████████████ (15 orders)
    user_4: ██████████ (10 orders)
    user_5: █████ (5 orders)
```

**3. Throughput (Line - đường)**
```
Orders/phút trên 20 phút gần nhất
    │     ╱╲
    │    ╱  ╲╱╲
    │   ╱      ╲╱╲
    ├──────────────→ (time)
    0  10:40  10:50 11:00
```

#### **Status (Real-time):**
```
🟢 Live — 10:45:30
(auto-refresh mỗi 5 giây)
```

### Bước 6: Test API Endpoints (Terminal D)

**Mở terminal/command prompt thứ 4:**

#### API 1: Summary
```bash
curl http://localhost:6066/metrics/summary
```

**Response:**
```json
{
    "total_orders": 50,
    "total_revenue": 45230.50,
    "avg_order_value": 904.61,
    "timestamp": "2024-01-15T10:45:30.123456"
}
```

#### API 2: Users
```bash
curl http://localhost:6066/metrics/users
```

**Response:**
```json
{
    "user_1": 12,
    "user_2": 8,
    "user_3": 15,
    "user_4": 10,
    "user_5": 5
}
```

#### API 3: Products
```bash
curl http://localhost:6066/metrics/products
```

**Response:**
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
    "Tablet": {
        "orders": 10,
        "revenue": 8564.00
    },
    ...
}
```

#### API 4: Throughput
```bash
curl http://localhost:6066/metrics/throughput
```

**Response:**
```json
{
    "10:40": 8,
    "10:41": 12,
    "10:42": 15,
    "10:43": 10,
    "10:44": 5
}
```

### Bước 7: Console Report (mỗi 25 giây)

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

### Bước 8: Dừng Demo 3

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

## 🔄 DEMO 4 (Advanced): Multi-Worker Scaling (15 phút)

Thể hiện: **Kafka Auto-rebalancing, Distributed State Consistency**

### Bước 1: Mở 4 Terminal

### Bước 2-4: Terminal A, B, C — 3 Workers

```bash
# Terminal A
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info

# Terminal B
python -m faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
python -m faust -A feature2_metrics worker -l info --web-port 6068
```

### Bước 5: Terminal D — Gửi Nhiều Data

```bash
cd Distributed-System-Faust
python producer.py -n 100 -i 0.2
```

### 🔑 **Quan Sát:**

**Khi Worker 3 khởi động:**
```
[10:50:00] INFO: ...Assignment change...
[10:50:01] INFO: Worker rebalanced
[10:50:02] INFO: Starting agent...
```

Kafka tự động chia partitions cho 3 workers!

**Verify:**
```bash
# Browser: http://localhost:6066/dashboard

# Tất cả 3 workers → same metrics!
# Example:
#   Terminal A: Tổng đơn: 50
#   Terminal B: Tổng đơn: 50
#   Terminal C: Tổng đơn: 50
# → LỖI nếu không bằng nhau!
```

---

## 📋 Checklist Demo

- [ ] **DEMO 1 (App Base)**
  - [ ] 2 workers running
  - [ ] Data flowing
  - [ ] "Tổng đơn" increases
  - [ ] Periodic report at 15s

- [ ] **DEMO 2 (DLQ)**
  - [ ] Retries showing (2s, 4s, 8s delays)
  - [ ] DLQ alerts visible
  - [ ] Success rate calculated

- [ ] **DEMO 3 (Metrics)**
  - [ ] Dashboard loads (http://localhost:6066/dashboard)
  - [ ] 5 metric cards visible
  - [ ] 3 charts rendering
  - [ ] Auto-refresh working
  - [ ] All 4 API endpoints respond

- [ ] **DEMO 4 (Multi-worker)**
  - [ ] 3 workers start
  - [ ] Rebalancing happens
  - [ ] Metrics consistent across all workers

---

## 🆘 Troubleshooting

### ❌ "Kafka connection refused"
```bash
# Check if Kafka is running
docker ps
# Output should show: faust-kafka and faust-zookeeper

# If not running:
docker-compose up -d
sleep 5
```

### ❌ "Port 6066 already in use"
```bash
# Find process using port
lsof -i :6066  # macOS/Linux
netstat -ano | findstr :6066  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
faust -A feature2_metrics worker --web-port 6070
```

### ❌ "No module named 'faust'"
```bash
pip install --upgrade -r requirements.txt
```

### ❌ Producer error "Connection refused"
```bash
# Make sure Kafka is running
docker-compose ps

# Restart Kafka
docker-compose restart
sleep 5

# Try producer again
python producer.py -n 10
```

### ❌ Dashboard không load
```bash
# Check if app is running
curl http://localhost:6066/metrics/summary

# If error, restart feature2_metrics
# Terminal: Ctrl+C, then restart
faust -A feature2_metrics worker -l info
```

---

## 💾 Dừng Toàn Bộ

```bash
# 1. Dừng Faust workers (Ctrl+C trong mỗi terminal)

# 2. Dừng Kafka
docker-compose down

# 3. Xóa dữ liệu (optional)
docker-compose down -v
```

---

## 📸 Screenshot Tips (để report)

### Lúc nào nên capture:

1. **DEMO 1:** "Tổng đơn" counter trên cả 2 terminals
2. **DEMO 2:** Retry delays + DLQ alert
3. **DEMO 3:** Dashboard + API responses
4. **DEMO 4:** 3 workers running + same metrics

### Dùng tools:
- **macOS:** Cmd+Shift+4 (screenshot)
- **Windows:** Windows+Shift+S (screenshot)
- **Linux:** PrintScreen
- **Browser:** F12 DevTools để capture JSON API

---

## ⏱️ Tổng Thời Gian

| Demo | Thời gian |
|------|-----------|
| Setup | 15 min |
| DEMO 1 | 15 min |
| DEMO 2 | 20 min |
| DEMO 3 | 25 min |
| DEMO 4 | 15 min |
| **Total** | **~90 min** |

---

## ✅ Kết Thúc

Sau khi hoàn thành 4 demos, bạn đã:
- ✅ Hiểu Topics, Agents, Tables
- ✅ Thấy distributed state sharing
- ✅ Thấy error handling (DLQ, retry)
- ✅ Thấy real-time monitoring
- ✅ Verify multi-worker scaling

**Ready to present!** 🎉

---

**Questions?** Refer to:
- [README.md](README.md) — Full documentation
- [FEATURES_DETAILED.md](FEATURES_DETAILED.md) — Concept explanations
- [STEP_BY_STEP.md](STEP_BY_STEP.md) — Detailed steps
