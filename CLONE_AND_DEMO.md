# 📥 Hướng Dẫn Pull Repository & Chạy Demo

Hướng dẫn chi tiết để **clone, setup, và demo** dự án từ GitHub.

---

## 🎯 Phần 1: Clone Repository

### Bước 1: Mở Terminal/Command Prompt

```bash
# macOS/Linux
open Terminal
# hoặc nhấn Cmd+Space, gõ "Terminal"

# Windows
nhấn Win+R, gõ "cmd", Enter
# hoặc Search "Command Prompt"
```

### Bước 2: Chọn thư mục cài đặt

```bash
# Đi đến Documents
cd ~/Documents
# hoặc Windows: cd Documents

# Hoặc thư mục khác bạn muốn
cd ~/Projects
```

### Bước 3: Clone Repository

```bash
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
```

**Expected output:**
```
Cloning into 'Distributed-System-Faust'...
remote: Enumerating objects: ...
Unpacking objects: 100% (X/X), done.
```

### Bước 4: Vào thư mục dự án

```bash
cd Distributed-System-Faust
ls -la
# hoặc Windows: dir
```

**Nên thấy tất cả các file (22 files):**
```
✅ .dockerignore
✅ .gitignore
✅ Dockerfile
✅ docker-compose.yml
✅ requirements.txt
✅ models.py
✅ app_base.py
✅ feature1_dlq.py
✅ feature2_metrics.py
✅ producer.py
✅ setup.sh
✅ test_setup.sh
✅ README.md
✅ QUICK_START.md
✅ ... (và các file .md khác)
```

---

## ⚙️ Phần 2: Setup Môi Trường

### Bước 1: Cài Python Dependencies

```bash
pip install -r requirements.txt
```

**Expected:**
```
Successfully installed:
- faust-streaming-0.10.14
- kafka-python-2.0.2
- aiohttp-3.9.5
- click-8.1.7
```

### Bước 2: Verify Installation

```bash
python -c "import faust; print('✅ Faust OK')"
python -c "from kafka import KafkaProducer; print('✅ Kafka Python OK')"
```

### Bước 3: Check Docker

```bash
docker --version
docker-compose --version
```

**Expected:**
```
Docker version 20.10+
Docker Compose version 1.29+
```

### Bước 4: Khởi động Kafka

```bash
docker-compose up -d
```

**Chờ 2-3 giây, rồi kiểm tra:**

```bash
docker ps
```

**Nên thấy 2 containers:**
```
CONTAINER ID   IMAGE                              STATUS
xxxxx          confluentinc/cp-kafka:7.5.0       Up 2 sec
yyyyy          confluentinc/cp-zookeeper:7.5.0   Up 3 sec
```

✅ **Setup hoàn tất!**

---

## 🎬 Phần 3: Chạy Demo

### Demo 1: Basic Topics, Agents, Tables (15 phút)

**File:** `app_base.py`  
**Mục đích:** Hiểu 3 khái niệm cốt lõi của Faust

#### Terminal A — Worker 1

```bash
python -m faust -A app_base worker -l info
```

Chờ khoảng 2-3 giây:
```
INFO: faust: Starting worker
INFO: faust: Worker ready
INFO: app.agent: Topic 'orders' partitions ready
```

#### Terminal B — Worker 2

**Mở tab/terminal mới:**

```bash
python -m faust -A app_base worker -l info --web-port 6067
```

#### Terminal C — Producer

**Mở tab/terminal thứ 3:**

```bash
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
✅ Đã gửi 15 orders vào topic 'orders'
```

#### Quan Sát Terminal A & B

**Bạn sẽ thấy order được xử lý:**

```
[10:30:15] ✅ [ORD-A1B2C3D4] Laptop x2 = $2198.00 | User user_2 — Tổng đơn: 1
[10:30:16] ✅ [ORD-C7D8E9F0] Tablet x3 = $1497.00 | User user_4 — Tổng đơn: 2
```

**🔑 Quan sát quan trọng:**
- "Tổng đơn" **liên tục tăng:** 1 → 2 → 3 → ... → 15
- **Cả 2 workers thấy cùng count** (dù xử lý message khác nhau)
- Điều này **chứng minh Faust Table được chia sẻ** giữa 2 workers!

#### Báo Cáo (mỗi 15 giây)

```
[10:30:30] ═══ TÓNG HỢP (App Base) ═══
  Người dùng: 5
  Tổng đơn: 15
  Tổng doanh thu: $15234.50
  Top sản phẩm:
    - Laptop: 5 đơn, $10990.00
    - Phone: 4 đơn, $3596.00
```

#### Dừng Demo 1

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

### Demo 2: DLQ + Exponential Backoff Retry (20 phút)

**File:** `feature1_dlq.py`  
**Mục đích:** Hiểu error handling với DLQ + retry

#### Terminal A — Worker 1

```bash
python -m faust -A feature1_dlq worker -l info
```

#### Terminal B — Worker 2

```bash
python -m faust -A feature1_dlq worker -l info --web-port 6067
```

#### Terminal C — Producer (40% fail-rate)

```bash
python producer.py -n 20 -i 1.5 -f 0.4
```

**Output:**
```
[  1/20] 📦 ORD-A1B2C3D4 | Laptop x2
[  2/20] 💀 FAIL-X5Y6Z7W8 | Phone x1    ← Sẽ fail
[  3/20] 📦 ORD-B5C6D7E8 | Tablet x3
```

#### Quan Sát Retry Logic

```
[10:35:20] ✅ OK    ORD-A1B2C3D4 — Laptop x2

[10:35:22] ⚠️  FAIL  FAIL-X5Y6Z7W8 (lần 1/3): Error message
           → Retry sau 2s...

[10:35:24] 🔄 RETRY 1/3 thất bại. Thử lại sau 4s

[10:35:28] 🔄 RETRY 2/3 thất bại. Thử lại sau 8s

[10:35:36] ❌ DLQ   FAIL-X5Y6Z7W8 — chuyển vào DLQ
```

**Backoff timing:** 2s → 4s → 8s

#### DLQ Alert

```
============================================================
  🚨 DLQ ALERT — 10:35:36
  Order ID    : FAIL-X5Y6Z7W8
  Lỗi cuối   : Sai định dạng order
  Đã retry   : 3 lần
============================================================
```

#### DLQ Report (mỗi 20 giây)

```
[10:35:55] 📊 Báo cáo DLQ:
  Nhận tổng    : 20
  Thành công   : 12  (60.0%)
  Retry đã gửi : 7
  Vào DLQ      : 1
```

#### Dừng Demo 2

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

### Demo 3: Real-time Metrics Dashboard (25 phút)

**File:** `feature2_metrics.py`  
**Mục đích:** Hiểu distributed metrics aggregation + visualization

#### Terminal A — Worker 1

```bash
python -m faust -A feature2_metrics worker -l info
```

#### Terminal B — Worker 2

```bash
python -m faust -A feature2_metrics worker -l info --web-port 6067
```

#### Terminal C — Producer

```bash
python producer.py -n 50 -i 0.5
```

#### Browser — Dashboard

**Mở trình duyệt → URL:** `http://localhost:6066/dashboard`

**Sẽ thấy:**

1. **5 Metric Cards (top):**
   ```
   📦 Total Orders: 50
   💰 Total Revenue: $45,230.50
   📈 Avg per Order: $904.61
   🛍️ Unique Products: 7
   👥 Unique Users: 5
   ```

2. **3 Charts:**
   - **Doughnut:** Revenue by Product (Laptop 30%, Phone 25%, ...)
   - **Bar:** Orders by User (user_1: 12, user_2: 8, ...)
   - **Line:** Throughput (last 20 minutes)

3. **Status:** 🟢 Live — [timestamp] (auto-refresh every 5s)

#### Test API Endpoints

**Terminal D — Test API:**

```bash
# API 1: Summary
curl http://localhost:6066/metrics/summary | python -m json.tool
# Output: {total_orders: 50, total_revenue: 45230.50, ...}

# API 2: Users
curl http://localhost:6066/metrics/users | python -m json.tool
# Output: {user_1: 12, user_2: 8, ...}

# API 3: Products
curl http://localhost:6066/metrics/products | python -m json.tool
# Output: {Laptop: {orders: 8, revenue: 15840}, ...}

# API 4: Throughput
curl http://localhost:6066/metrics/throughput | python -m json.tool
# Output: {10:40: 8, 10:41: 12, ...}
```

#### Console Report (mỗi 25 giây)

```
[10:46:15] ═══ METRICS REPORT ═══
  Tổng đơn  : 50
  Doanh thu : $45230.50
  Avg/đơn   : $904.61
  Top products:
    • Laptop: $15840.00
    • Phone: $10788.00
```

#### Dừng Demo 3

```bash
# Terminal A: Ctrl+C
# Terminal B: Ctrl+C
```

---

## 🔄 Demo 4 (Advanced): Multi-Worker Scaling (15 phút)

Để thấy Kafka **auto-rebalancing** với 3+ workers

#### Start 3 Workers

```bash
# Terminal A
python -m faust -A feature2_metrics worker -l info

# Terminal B
python -m faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
python -m faust -A feature2_metrics worker -l info --web-port 6068
```

#### Send More Data

```bash
# Terminal D
python producer.py -n 100 -i 0.2
```

#### Verify

- **Dashboard:** http://localhost:6066/dashboard
  - Thấy metrics tích lũy từ **3 workers cùng lúc**
  - Dữ liệu luôn **consistent** (không bị duplicate hoặc miss)

- **Verify Rebalancing:**
  - Khi worker 3 start, bạn sẽ thấy `INFO: Assignment change`
  - Kafka tự chia partition cho 3 workers

---

## 📋 Cleanup

### Dừng Faust Workers

```bash
# Mỗi terminal: Ctrl+C
```

### Dừng Kafka

```bash
docker-compose down
```

### Xóa Data (optional)

```bash
docker-compose down -v
```

---

## 📸 Hệ Thống Checklist

- [ ] Clone repository
- [ ] Install dependencies
- [ ] Docker containers running (2 should show)
- [ ] Demo 1: 2 workers + producer → "Tổng đơn" increases
- [ ] Demo 2: Retry delays visible (2s, 4s, 8s)
- [ ] Demo 2: DLQ alerts showing
- [ ] Demo 3: Dashboard loads on localhost:6066
- [ ] Demo 3: 5 cards + 3 charts visible
- [ ] Demo 3: APIs responding (curl test)
- [ ] Demo 4: 3 workers running + metrics consistent

---

## 🆘 Troubleshooting

### **Docker containers not running**
```bash
docker ps
# If empty:
docker-compose up -d
```

### **"faust command not found"**
```bash
pip install faust-streaming
```

### **Port already in use**
```bash
# Find what's using port 6066
lsof -i :6066  # macOS/Linux
netstat -ano | findstr :6066  # Windows

# Kill the process or use different port
faust -A feature2_metrics worker --web-port 6070
```

### **Producer error: Connection refused**
```bash
# Make sure Kafka is running
docker ps
docker-compose restart
sleep 5
python producer.py -n 10
```

---

## 📚 Next Steps

1. **Read Documentation:**
   - [README.md](README.md) — Full documentation
   - [QUICK_START.md](QUICK_START.md) — Quick reference

2. **Explore Source Code:**
   - [models.py](models.py) — Data model
   - [app_base.py](app_base.py) — Baseline
   - [feature1_dlq.py](feature1_dlq.py) — Error handling
   - [feature2_metrics.py](feature2_metrics.py) — Monitoring

3. **Learn More:**
   - [FEATURES_DETAILED.md](FEATURES_DETAILED.md) — Architecture
   - [STEP_BY_STEP.md](STEP_BY_STEP.md) — Detailed walkthrough

---

✅ **Ready to demo!** 🚀

Total time to complete all 4 demos: **~75 minutes**
