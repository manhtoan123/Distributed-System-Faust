# 👨‍🏫 Rubric & Grading Guide (Cho Giáo viên)

## 📋 Tóm tắt Bài tập

**Chủ đề:** Faust — Distributed Stream Processing for Python  
**Yêu cầu:** Setup, thực nghiệm, + 2 tính năng mới  
**Thời gian:** 4-5 giờ  
**Độ khó:** Medium-Hard  

---

## ✅ Yêu cầu Hoàn thành

### 1. Setup & Configuration (20%)

- [x] **docker-compose.yml:** Kafka + Zookeeper chạy đúng
- [x] **requirements.txt:** Dependencies chính xác (faust-streaming, kafka-python, aiohttp)
- [x] **Dockerfile:** Container image build được
- [x] **setup.sh:** Script cài đặt tự động
- [x] **Python 3.9+:** Verified

**Kiểm tra:** `docker-compose up -d && docker ps` (nên thấy 2 containers)

### 2. Basic Demo (app_base.py) — 15%

Minh họa 3 khái niệm cốt lõi:

- [x] **Topic:** `orders` topic được tạo + consume đúng
- [x] **Agent:** `process_orders` agent chạy async + xử lý message
- [x] **Table:** `order_count_by_user`, `total_revenue` chia sẻ state giữa workers
- [x] **Distributed:** 2+ workers thấy consistent state

**Output expected:**
```
[timestamp] ✅ [ORD-xxx] product x qty = $price | User user_id — Tổng đơn: N
[timestamp] ═══ TÓNG HỢP (App Base) ═══
  Người dùng: 5
  Tổng đơn: 15
  Tổng doanh thu: $15234.50
```

**Kiểm tra:** Run 2 workers + producer, verify "Tổng đơn" tăng nhất quán

### 3. Feature 1: DLQ + Retry (25%)

Dead Letter Queue + Exponential Backoff Retry

**Requirements:**
- [x] **Topics:** 
  - `orders` → nhập
  - `orders_retry` → retry
  - `orders_dlq` → thất bại cuối cùng

- [x] **Agents:**
  - `main_processor`: xử lý, nếu fail → retry_count++, gửi `orders_retry`
  - `retry_processor`: retry lại, nếu fail max lần → gửi `orders_dlq`
  - `dlq_monitor`: log alert

- [x] **Exponential Backoff:**
  - Retry 1: chờ 2^1 = 2s
  - Retry 2: chờ 2^2 = 4s
  - Retry 3: chờ 2^3 = 8s
  - Retry > 3: → DLQ

- [x] **Distributed Error Tracking:**
  - `dlq_stats` Table (distributed, sync via Kafka)
  - Track: total, success, retry_sent, dlq

- [x] **Periodic Report:**
  - Mỗi 20s, in báo cáo success rate

**Output expected:**
```
[timestamp] ✅ OK    ORD-ABC123 — Laptop x2
[timestamp] ⚠️  FAIL  FAIL-XYZ789 (lần 1/3): Error message → Retry sau 2s
[timestamp] 🔄 RETRY 1/3 thất bại → Thử lại sau 4s
[timestamp] ❌ DLQ   FAIL-XYZ789 hết lần retry

============================================================
  🚨 DLQ ALERT — timestamp
  Order ID    : FAIL-XYZ789
  Lỗi cuối   : Error message
  Đã retry   : 3 lần
============================================================

[timestamp] 📊 Báo cáo DLQ:
  Nhận tổng    : 20
  Thành công   : 12  (60.0%)
  Retry đã gửi : 7
  Vào DLQ      : 1
```

**Kiểm tra:** 
```bash
python producer.py -n 20 -i 1.5 -f 0.4  # 40% fail-rate
# Verify: retry delays (2s, 4s, 8s)
# Verify: DLQ alerts after 3 retries
# Verify: dlq_stats consistency (2 workers)
```

### 4. Feature 2: Distributed Metrics Dashboard (25%)

Real-time metrics + HTTP API + Interactive Dashboard

**Requirements:**
- [x] **Topics:**
  - `orders` (partitions=3) → input

- [x] **Agents:**
  - `metrics_collector`: collect all metrics, update tables

- [x] **Tables (5 total, distributed):**
  - `global_stats`: total_orders, total_revenue, avg_order_value
  - `orders_by_user`: dict by user_id
  - `revenue_by_prod`: dict by product
  - `orders_by_prod`: dict by product
  - `throughput`: dict by minute

- [x] **HTTP API (4 endpoints):**
  - `GET /metrics/summary` → JSON (total, revenue, avg)
  - `GET /metrics/users` → JSON {user_id: count}
  - `GET /metrics/products` → JSON {product: {orders, revenue}}
  - `GET /metrics/throughput` → JSON {minute: count}

- [x] **Dashboard:**
  - `GET /dashboard` → HTML page
  - Display: 5 metric cards (total, revenue, avg, products, users)
  - Display: 3 charts (Chart.js)
    - Doughnut: revenue by product
    - Bar: orders by user
    - Line: throughput (last 20 minutes)
  - Auto-refresh: 5 giây

- [x] **Periodic Report:**
  - Mỗi 25s, in console report (top products)

**Output expected:**
```
[timestamp] [METRICS] ORD-ABC123 | Laptop x2 = $1798.00 | Tổng đơn: 23

[timestamp] ═══ METRICS REPORT ═══
  Tổng đơn  : 50
  Doanh thu : $45230.50
  Avg/đơn   : $904.61
  Top products:
    • Laptop: $15840.00
    • Phone: $10788.00
```

**Dashboard:**
- 5 cards visible
- 3 charts updating
- Auto-refresh working (✅ message visible)

**API Response (curl):**
```json
GET /metrics/summary
{
    "total_orders": 50,
    "total_revenue": 45230.50,
    "avg_order_value": 904.61
}
```

**Kiểm tra:**
```bash
# 1. Dashboard loads
curl http://localhost:6066/dashboard | grep "Faust"

# 2. API endpoints work
curl http://localhost:6066/metrics/summary | python -m json.tool
curl http://localhost:6066/metrics/users | python -m json.tool

# 3. Multi-worker consistency
# Run 3 workers, verify all see same metrics
```

### 5. Distributed Processing Verification (10%)

Multi-worker scaling + data consistency

- [x] **2+ Workers:** Kafka partitions tự divide
- [x] **State Sharing:** Faust Tables sync tự động (via Kafka changelog)
- [x] **No Manual Sync:** Không cần locking, RPC, hoặc manual aggregation
- [x] **Fail-over:** If worker dies, Kafka rebalances, others continue

**Kiểm tra:**
```bash
# Terminal 1: Worker 1
faust -A feature2_metrics worker -l info

# Terminal 2: Worker 2
faust -A feature2_metrics worker -l info --web-port 6067

# Terminal 3: Producer
python producer.py -n 50 -i 0.3

# Verify: both workers process orders in real-time
# Verify: metrics consistent (total_orders same in both)
# Verify: dashboard shows combined metrics
```

---

## 📝 Documentation (5%)

- [x] **README.md:** ≥10KB, comprehensive
  - Setup guide
  - 3 concepts explanation
  - Each app walkthrough
  - Troubleshooting
  - Extensions ideas

- [x] **QUICK_START.md:** ≤10 phút để chạy
- [x] **STEP_BY_STEP.md:** Chi tiết từng bước
- [x] **FEATURES_DETAILED.md:** Deep dive architecture
- [x] **COMMANDS_REFERENCE.md:** Copy-paste ready
- [x] **PROJECT_SUMMARY.md:** Tóm tắt dự án

---

## 📏 Scoring Rubric

### Total: 100 points

| Component | Points | Criteria |
|-----------|--------|----------|
| **Setup** | 20 | Docker, Python, Kafka all working |
| **app_base.py** | 15 | Topics, Agents, Tables, distributed state |
| **feature1_dlq.py** | 25 | DLQ, retry, backoff, error tracking, multi-worker consistency |
| **feature2_metrics.py** | 25 | Tables, API, dashboard, real-time metrics, distributed |
| **Distributed Verification** | 10 | Multi-worker scaling, auto sync, no manual sync |
| **Documentation** | 5 | README, guides, code comments |

---

## 🎯 Grading Guide

### A+ (95-100)
- ✅ All 5 components working perfectly
- ✅ Clean code with comments
- ✅ Comprehensive documentation
- ✅ Demonstrates deep understanding
- ✅ No bugs or issues
- **Extra:** Extensions (windowing, joins, persistence, etc.)

### A (90-94)
- ✅ All 5 components working
- ✅ Good code quality
- ✅ Good documentation
- ✅ Understands concepts
- ⚠️ Minor issues, easily fixed

### B (80-89)
- ✅ All 5 components mostly working
- ✅ Decent code
- ✅ Decent documentation
- ⚠️ Some bugs or edge cases
- ⚠️ Partial understanding

### C (70-79)
- ✅ Basic features working
- ⚠️ app_base.py simple, but works
- ⚠️ One feature incomplete or buggy
- ⚠️ Limited documentation
- ⚠️ Distributed processing not verified

### D (60-69)
- ⚠️ Setup issues
- ⚠️ Features partially implemented
- ⚠️ Many bugs
- ⚠️ Poor documentation
- ❌ Distributed processing doesn't work

### F (<60)
- ❌ Major issues
- ❌ Doesn't run
- ❌ Missing features
- ❌ No documentation

---

## 🔍 How to Grade

### Step 1: Test Setup (5 min)
```bash
# Verify files exist
ls *.py *.md docker-compose.yml requirements.txt

# Verify dependencies
pip install -r requirements.txt

# Verify Kafka runs
docker-compose up -d && docker ps
```

### Step 2: Test app_base.py (10 min)
```bash
# Terminal 1
faust -A app_base worker -l info

# Terminal 2
faust -A app_base worker -l info --web-port 6067

# Terminal 3
python producer.py -n 15 -i 0.8

# Verify: output matches STEP_BY_STEP.md expected output
# Verify: "Tổng đơn" increases consistently
# Verify: both workers show same count
```

### Step 3: Test feature1_dlq.py (10 min)
```bash
# Terminal 1
faust -A feature1_dlq worker -l info

# Terminal 2
faust -A feature1_dlq worker -l info --web-port 6067

# Terminal 3
python producer.py -n 20 -i 1.5 -f 0.4

# Verify: retry delays (2s, 4s, 8s) visible
# Verify: DLQ alerts printed
# Verify: dlq_stats consistency
# Check: success rate calculation
```

### Step 4: Test feature2_metrics.py (15 min)
```bash
# Terminal 1
faust -A feature2_metrics worker -l info

# Terminal 2
faust -A feature2_metrics worker -l info --web-port 6067

# Terminal 3
python producer.py -n 50 -i 0.5

# Test APIs
curl http://localhost:6066/metrics/summary
curl http://localhost:6066/metrics/users
curl http://localhost:6066/metrics/products
curl http://localhost:6066/metrics/throughput

# Open dashboard
curl http://localhost:6066/dashboard | grep -c "Faust"
# Should return 1 (HTML contains "Faust")

# Browser: http://localhost:6066/dashboard
# Verify: 5 cards visible
# Verify: 3 charts rendering
# Verify: auto-refresh working
```

### Step 5: Test Distributed Processing (10 min)
```bash
# Add 3rd worker
faust -A feature2_metrics worker -l info --web-port 6068

# Verify Kafka rebalancing happens
# Send more data
python producer.py -n 100 -i 0.2

# Verify:
# - All 3 workers process concurrently
# - Metrics remain consistent
# - Dashboard shows aggregated metrics from all 3
```

### Step 6: Review Documentation (5 min)
- Check README.md size (should be ~15-20KB)
- Verify QUICK_START.md has working commands
- Verify STEP_BY_STEP.md has expected outputs
- Check code has comments

---

## ⭐ Bonus Points (5-10%)

- **Windowing:** Add time-window aggregation
- **Joins:** Join 2 topics
- **Persistence:** Save DLQ to database
- **Schema Registry:** Use Avro/Protobuf
- **Monitoring:** Export Prometheus metrics
- **Testing:** Unit or integration tests
- **Deployment:** Kubernetes manifests
- **Performance:** Benchmarking results

---

## ❌ Common Issues & How to Handle

### Issue: Docker containers won't start
- **Check:** `docker logs faust-kafka`
- **Solution:** Usually disk space or port already in use
- **Grade:** Deduct 10 points, allow re-submission

### Issue: app_base.py doesn't show distributed state
- **Check:** Are 2 workers actually running?
- **Check:** Is producer actually sending data?
- **Solution:** Might need to clarify Faust Table behavior
- **Grade:** Deduct 20 points, ask for explanation

### Issue: feature1_dlq.py doesn't show retries
- **Check:** Is fail-rate high enough?
- **Solution:** Ask to rerun with `-f 0.5` or `-f 0.8`
- **Grade:** Deduct 10 points

### Issue: feature2_metrics.py dashboard doesn't load
- **Check:** Port 6066 already in use?
- **Check:** HTTP server started?
- **Solution:** Change port, restart
- **Grade:** Deduct 15 points

### Issue: APIs return 404
- **Check:** Is the app running on correct port?
- **Check:** Are routes registered?
- **Solution:** Check code, restart app
- **Grade:** Deduct 15 points

---

## 📞 Questions to Ask During Review

1. **Why did you choose Faust over other stream processing libraries?**
2. **Explain the exponential backoff in feature1_dlq.py**
3. **How does the Faust Table ensure consistency across workers?**
4. **What happens if a worker dies? How does Kafka handle it?**
5. **Why is concurrency important in metrics_collector?**
6. **What's the difference between a Table and a View?**
7. **How would you extend this to 100+ workers?**
8. **What are failure modes in distributed streaming?**
9. **How would you integrate this with external systems (email, Slack)?**
10. **Can you explain the dashboard refresh mechanism?**

---

## 📊 Sample Grades

### Student A (95/100)
- ✅ All working perfectly
- ✅ Clean code with docstrings
- ✅ 20KB+ documentation
- ✅ Extra: Added Windowing feature
- ⭐ Bonus: +5 points

### Student B (85/100)
- ✅ All features work
- ✅ Good understanding
- ⚠️ Some minor bugs (fixed during review)
- ⚠️ Documentation could be better

### Student C (70/100)
- ✅ Basic features work
- ⚠️ Distributed processing partially verified
- ⚠️ Documentation incomplete
- ⚠️ Some confusion about Faust concepts

### Student D (50/100)
- ⚠️ Setup issues
- ⚠️ app_base.py works, but feature1 and 2 have bugs
- ⚠️ Very limited documentation
- ❌ Doesn't demonstrate understanding

---

## 📋 Final Checklist for Grader

- [ ] Files exist and are readable
- [ ] docker-compose.yml works
- [ ] Python dependencies install
- [ ] app_base.py runs with 2 workers
- [ ] feature1_dlq.py shows DLQ + retry
- [ ] feature2_metrics.py dashboard loads
- [ ] All 4 APIs respond correctly
- [ ] Multi-worker consistency verified
- [ ] Documentation ≥ 10KB
- [ ] Code is readable and has comments

---

**Total Time to Grade:** 60 minutes per submission

**Ready to submit?** Checklist complete ✅
