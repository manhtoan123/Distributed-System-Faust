# 📖 HƯỚNG DẪN DEMO TOÀN BỘ - TẤT CẢ TRONG 1 FILE

**Repository:** https://github.com/manhtoan123/Distributed-System-Faust

---

## ⚡ QUICK START (5 PHÚT)

```bash
# Bước 1: Clone
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust

# Bước 2: Setup
pip install -r requirements.txt
docker-compose up -d

# Bước 3: Chạy Demo (chọn 1 trong 4 demos ở dưới)
```

---

## 🎬 4 DEMOS AVAILABLE

| # | Tên | Thời gian | Lệnh |
|---|-----|----------|------|
| **1** | App Base | 15 min | `python -m faust -A app_base worker -l info` |
| **2** | DLQ + Retry | 20 min | `python -m faust -A feature1_dlq worker -l info` |
| **3** | Metrics Dashboard | 25 min | `python -m faust -A feature2_metrics worker -l info` |
| **4** | Multi-Worker | 15 min | 3x `python -m faust -A feature2_metrics worker -l info` |

---

# DEMO 1: App Base (Topics, Agents, Tables)

**Thời gian:** 15 phút  
**Mục đích:** Hiểu 3 khái niệm cốt lõi của Faust: Topic, Agent, Distributed Table

## Bước 1: Mở 3 Terminal/Tab

## Bước 2: Terminal A — Worker 1

```bash
cd Distributed-System-Faust
python -m faust -A app_base worker -l info
```

**Chờ 2-3 giây, bạn sẽ thấy:**

```
[2024-01-15 10:30:00,123] INFO: faust: Starting worker
[2024-01-15 10:30:01,234] INFO: faust: Worker ready (pid=12345)
[2024-01-15 10:30:02,345] INFO: app.agent: Topic 'orders' partitions ready
```

⏸️ **Để Terminal A chạy, đừng đóng!**

## Bước 3: Terminal B — Worker 2 (để demo distributed)

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

## Bước 4: Terminal C — Gửi Test Data

**Mở tab/terminal thứ 3:**

```bash
cd Distributed-System-Faust
python producer.py -n 15 -i 0.8
```

**Expected output:**

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

## Bước 5: Quan Sát Terminal A & B

**Terminal A Output (xử lý partition 0):**

```
[10:30:15] ✅ [ORD-A1B2C3D4] Laptop x2 = $2198.00 | User user_2 — Tổng đơn: 1
[10:30:16] ✅ [ORD-C7D8E9F0] Tablet x3 = $1497.00 | User user_4 — Tổng đơn: 2
[10:30:17] ✅ [ORD-E9F0A1B2] Phone x1 = $899.00 | User user_1 — Tổng đơn: 3
```

**Terminal B Output (xử lý partition 1, 2):**

```
[10:30:15] ✅ [ORD-B5C6D7E8] Phone x1 = $899.00 | User user_3 — Tổng đơn: 4
[10:30:16] ✅ [ORD-D8E9F0A1] Watch x2 = $598.00 | User user_5 — Tổng đơn: 5
[10:30:17] ✅ [ORD-F0A1B2C3] Keyboard x1 = $149.00 | User user_2 — Tổng đơn: 6
```

## 🔑 Quan Sát Quan Trọng

**Nhìn cột "Tổng đơn": `1 → 2 → 3 → 4 → 5 → 6 → ... → 15`**

**Điều này chứng minh:**
- ✅ Worker A xử lý một số order
- ✅ Worker B xử lý những order khác
- ✅ **Cả 2 workers CHIA SẼ cùng một Faust Table**
- ✅ Dữ liệu luôn nhất quán (không cần locking!)

## Bước 6: Báo Cáo Periodic (chờ ~15 giây)

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

## Bước 7: Dừng Demo 1

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

# DEMO 2: Feature 1 — DLQ + Retry (20 phút)

**Thời gian:** 20 phút  
**Mục đích:** Hiểu error handling với DLQ + exponential backoff retry

## Bước 1: Mở 3 Terminal Mới

## Bước 2: Terminal A — Worker 1

```bash
cd Distributed-System-Faust
python -m faust -A feature1_dlq worker -l info
```

## Bước 3: Terminal B — Worker 2

```bash
cd Distributed-System-Faust
python -m faust -A feature1_dlq worker -l info --web-port 6067
```

## Bước 4: Terminal C — Gửi Data (40% fail-rate)

```bash
cd Distributed-System-Faust
python producer.py -n 20 -i 1.5 -f 0.4
```

**Output từ producer:**

```
📤 Gửi 20 đơn hàng
   Interval: 1.5s | Fail rate: 40.0%

[  1/20] 📦 ORD-A1B2C3D4 | Laptop x2 = $2198.00
[  2/20] 💀 FAIL-X5Y6Z7W8 | Phone x1 = $899.00      ← Thất bại (sẽ retry)
[  3/20] 📦 ORD-B5C6D7E8 | Tablet x3 = $1497.00
...
```

## Bước 5: Quan Sát Retry Logic (Terminal A & B)

**Bạn sẽ thấy các order thất bại RETRY tự động:**

```
[10:35:20] ✅ OK    ORD-A1B2C3D4 — Laptop x2

[10:35:22] ⚠️  FAIL  FAIL-X5Y6Z7W8 (lần 1/3): Sai định dạng order: FAIL-X5Y6Z7W8
           → Retry sau 2s...

[10:35:24] 🔄 RETRY 1/3 thất bại cho FAIL-X5Y6Z7W8. Thử lại sau 4s

[10:35:28] 🔄 RETRY 2/3 thất bại cho FAIL-X5Y6Z7W8. Thử lại sau 8s

[10:35:36] ❌ DLQ   FAIL-X5Y6Z7W8 — chuyển vào DLQ
```

## 🔑 Exponential Backoff Timing

| Lần | Chờ | Giây |
|-----|-----|------|
| Retry 1 | 2^1 = | 2s |
| Retry 2 | 2^2 = | 4s |
| Retry 3 | 2^3 = | 8s |
| Tiếp theo | → DLQ | Alert |

## Bước 6: DLQ Alert (sau mỗi order fail 3 lần)

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

## Bước 7: DLQ Report (mỗi 20 giây)

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

## Bước 8: Dừng Demo 2

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

# DEMO 3: Feature 2 — Metrics Dashboard (25 phút)

**Thời gian:** 25 phút  
**Mục đích:** Hiểu distributed metrics gathering + real-time visualization

## Bước 1: Mở 3 Terminal Mới

## Bước 2: Terminal A — Worker 1

```bash
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info
```

## Bước 3: Terminal B — Worker 2

```bash
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info --web-port 6067
```

## Bước 4: Terminal C — Gửi Test Data (liên tục)

```bash
cd Distributed-System-Faust
python producer.py -n 50 -i 0.5
```

## Bước 5: Mở Browser & Truy cập Dashboard

**URL:** `http://localhost:6066/dashboard`

## 🎨 Dashboard sẽ hiển thị

### **5 Metric Cards (top):**

```
📦 Total Orders          💰 Total Revenue        📈 Avg per Order
      50                      $45,230.50               $904.61

🛍️ Unique Products       👥 Unique Users
        7                          5
```

### **3 Charts (dưới):**

**1. Revenue by Product (Doughnut - tròn)**
- Laptop: 30% (xanh)
- Phone: 25% (xanh lá)
- Tablet: 20% (cam)
- Watch: 15% (tím)
- Others: 10%

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

### **Status (Real-time):**

```
🟢 Live — 10:45:30
(auto-refresh mỗi 5 giây)
```

## Bước 6: Test API Endpoints (Terminal D)

**Mở terminal/command prompt thứ 4:**

### API 1: Summary

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

### API 2: Users

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

### API 3: Products

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
    }
}
```

### API 4: Throughput

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

## Bước 7: Console Report (mỗi 25 giây)

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

## Bước 8: Dừng Demo 3

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

# DEMO 4 (Advanced): Multi-Worker Scaling (15 phút)

**Thời gian:** 15 phút  
**Mục đích:** Thấy Kafka auto-rebalance partitions với 3+ workers

## Bước 1: Mở 4 Terminal

## Bước 2-4: Terminal A, B, C — 3 Workers

```bash
# Terminal A
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info

# Terminal B
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
cd Distributed-System-Faust
python -m faust -A feature2_metrics worker -l info --web-port 6068
```

## Bước 5: Terminal D — Gửi Nhiều Data

```bash
cd Distributed-System-Faust
python producer.py -n 100 -i 0.2
```

## 🔑 Quan Sát

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

### ❌ "python -m faust: No module named faust"

```bash
# Fix 1: Cài lại
pip install --upgrade faust-streaming

# Fix 2: Check version
python -c "import faust; print(faust.__version__)"
```

### ❌ "Kafka connection refused"

```bash
# Check if Kafka is running
docker ps
# Output should show: faust-kafka and faust-zookeeper

# If not running:
docker-compose up -d
sleep 3
```

### ❌ "Port 6066 already in use"

```bash
# Find process using port
lsof -i :6066  # macOS/Linux
netstat -ano | findstr :6066  # Windows

# Kill process or use different port
python -m faust -A feature2_metrics worker --web-port 6070
```

### ❌ Producer error "Connection refused"

```bash
# Make sure Kafka is running
docker ps
docker-compose restart
sleep 5
python producer.py -n 10
```

### ❌ Dashboard không load

```bash
# Check if app is running
curl http://localhost:6066/metrics/summary

# If error, restart feature2_metrics
# Terminal: Ctrl+C, then restart
python -m faust -A feature2_metrics worker -l info
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

## 🎓 Kỳ Vọng Sau Demo

Người xem sẽ hiểu:

✅ **Faust Fundamentals** — Topics, Agents, Tables  
✅ **Distributed State Sharing** — Faust Tables auto-sync  
✅ **Error Handling** — DLQ + Exponential Backoff  
✅ **Real-time Monitoring** — Metrics aggregation  
✅ **Fault Tolerance** — Auto-rebalancing  
✅ **Scaling** — Multi-worker support  

---

## 📍 GITHUB REPOSITORY

**URL:** https://github.com/manhtoan123/Distributed-System-Faust

✅ **Sẵn sàng clone và chạy demo!**

---

## 🎬 BẮNG ĐẦU NGAY HÔM NAY

```bash
# 1. Clone repo
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust

# 2. Setup
pip install -r requirements.txt
docker-compose up -d

# 3. Chọn demo (chạy 3 terminals)
# Demo 3 (Fastest): python -m faust -A feature2_metrics worker -l info
# Demo 1: python -m faust -A app_base worker -l info
# Demo 2: python -m faust -A feature1_dlq worker -l info

# 4. View results
# Browser: http://localhost:6066/dashboard (Demo 3 only)
```

---

✅ **Sẵn sàng demo! 🚀**
