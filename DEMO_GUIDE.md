# 🎬 HƯỚNG DẪN DEMO - TẤT CẢ TRONG 1 FILE

**Repository:** https://github.com/manhtoan123/Distributed-System-Faust

---

## ⚡ QUICK START

```bash
# 1. Clone
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust

# 2. Setup
pip install -r requirements.txt
docker-compose up -d

# 3. Chạy demo (chọn 1 trong 4)
```

---

## 🎬 4 DEMOS

| Demo | Thời gian | Lệnh |
|------|----------|------|
| 1. App Base | 15 min | `python -m faust -A app_base worker -l info` |
| 2. DLQ + Retry | 20 min | `python -m faust -A feature1_dlq worker -l info` |
| 3. Metrics Dashboard | 25 min | `python -m faust -A feature2_metrics worker -l info` |
| 4. Multi-Worker | 15 min | 3x workers |

---

# DEMO 1: App Base (15 min)

**Mục đích:** Topics, Agents, Distributed Tables

## Terminal A — Worker 1
```bash
python -m faust -A app_base worker -l info
```

## Terminal B — Worker 2
```bash
python -m faust -A app_base worker -l info --web-port 6067
```

## Terminal C — Producer
```bash
python producer.py -n 15 -i 0.8
```

## 🔑 Quan Sát

**Terminal A & B sẽ hiển thị:**
```
[10:30:15] ✅ [ORD-A1B2C3D4] Laptop x2 | User user_2 — Tổng đơn: 1
[10:30:16] ✅ [ORD-B5C6D7E8] Phone x1 | User user_3 — Tổng đơn: 2
[10:30:17] ✅ [ORD-C7D8E9F0] Tablet x3 | User user_4 — Tổng đơn: 3
```

**Quan trọng:** "Tổng đơn" liên tục tăng 1→2→3→...→15
- Dù 2 workers xử lý message khác nhau
- Nhưng cả 2 chia sẻ cùng Faust Table
- **Chứng minh distributed state sharing!**

**Báo cáo (15 giây):**
```
[10:30:30] ═══ TÓNG HỢP ═══
  Người dùng: 5
  Tổng đơn: 15
  Tổng doanh thu: $15234.50
```

---

# DEMO 2: DLQ + Retry (20 min)

**Mục đích:** Error handling với exponential backoff

## Terminal A — Worker 1
```bash
python -m faust -A feature1_dlq worker -l info
```

## Terminal B — Worker 2
```bash
python -m faust -A feature1_dlq worker -l info --web-port 6067
```

## Terminal C — Producer (40% fail)
```bash
python producer.py -n 20 -i 1.5 -f 0.4
```

## 🔑 Quan Sát

**Retry logic với exponential backoff:**
```
[10:35:22] ⚠️  FAIL  FAIL-X5Y6Z7W8 (lần 1/3)
           → Retry sau 2s...

[10:35:24] 🔄 RETRY 1/3 thất bại. Thử lại sau 4s

[10:35:28] 🔄 RETRY 2/3 thất bại. Thử lại sau 8s

[10:35:36] ❌ DLQ   FAIL-X5Y6Z7W8 — chuyển vào DLQ
```

**Timing:** 2s → 4s → 8s (exponential: 2^n)

**DLQ Alert:**
```
🚨 DLQ ALERT
  Order ID: FAIL-X5Y6Z7W8
  Lỗi: Sai định dạng order
  Đã retry: 3 lần
```

**Report (20 giây):**
```
📊 Báo cáo DLQ:
  Nhận tổng: 20
  Thành công: 12 (60.0%)
  Vào DLQ: 1
```

---

# DEMO 3: Metrics Dashboard (25 min) ⭐ RECOMMENDED

**Mục đích:** Real-time metrics + visualization

## Terminal A — Worker 1
```bash
python -m faust -A feature2_metrics worker -l info
```

## Terminal B — Worker 2
```bash
python -m faust -A feature2_metrics worker -l info --web-port 6067
```

## Terminal C — Producer
```bash
python producer.py -n 50 -i 0.5
```

## Browser — Dashboard
```
http://localhost:6066/dashboard
```

## 🎨 Dashboard Hiển Thị

**5 Metric Cards:**
- 📦 Total Orders: 50
- 💰 Total Revenue: $45,230.50
- 📈 Avg per Order: $904.61
- 🛍️ Products: 7
- 👥 Users: 5

**3 Charts:**
1. Revenue by Product (Doughnut)
2. Orders by User (Bar)
3. Throughput (Line - 20 min)

**Status:** 🟢 Live (auto-refresh 5 giây)

## Test APIs

```bash
# Summary
curl http://localhost:6066/metrics/summary

# Users
curl http://localhost:6066/metrics/users

# Products
curl http://localhost:6066/metrics/products

# Throughput
curl http://localhost:6066/metrics/throughput
```

---

# DEMO 4: Multi-Worker Scaling (15 min)

**Mục đích:** Kafka auto-rebalancing + consistency

## Terminal A, B, C — 3 Workers
```bash
# Terminal A
python -m faust -A feature2_metrics worker -l info

# Terminal B
python -m faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
python -m faust -A feature2_metrics worker -l info --web-port 6068
```

## Terminal D — Producer
```bash
python producer.py -n 100 -i 0.2
```

## 🔑 Quan Sát

**Khi Worker 3 start:**
```
[10:50:00] INFO: Assignment change...
[10:50:01] INFO: Worker rebalanced
```

Kafka tự động chia partitions cho 3 workers!

**Verify Dashboard:**
- Tất cả 3 workers → same metrics ✅
- Không bị duplicate hoặc miss ✅
- Auto-rebalancing works ✅

---

## ✅ Checklist

- [ ] 2 workers chạy (Demo 1, 2)
- [ ] Data flowing
- [ ] "Tổng đơn" tăng (Demo 1)
- [ ] Retry delays 2s, 4s, 8s (Demo 2)
- [ ] DLQ alerts (Demo 2)
- [ ] Dashboard loads (Demo 3)
- [ ] 5 cards + 3 charts visible (Demo 3)
- [ ] APIs respond JSON (Demo 3)
- [ ] 3 workers consistent (Demo 4)

---

## 🆘 Troubleshooting

### "python -m faust: No module named faust"
```bash
pip install --upgrade faust-streaming
```

### "Kafka connection refused"
```bash
docker-compose up -d
docker ps
```

### "Port 6066 already in use"
```bash
python -m faust -A feature2_metrics worker --web-port 6070
```

### "Dashboard không load"
```bash
curl http://localhost:6066/metrics/summary
```

---

## 🛑 Cleanup

```bash
# Dừng workers: Ctrl+C mỗi terminal

# Dừng Kafka
docker-compose down

# Xóa data (optional)
docker-compose down -v
```

---

## ⏱️ Thời Gian

| Demo | Thời gian |
|------|----------|
| Setup | 15 min |
| Demo 1 | 15 min |
| Demo 2 | 20 min |
| Demo 3 | 25 min |
| Demo 4 | 15 min |
| **Total** | **90 min** |

**Hoặc chỉ Demo 3:** 40 min (nhanh nhất + đẹp nhất)

---

## 🎓 Key Points

✅ **Distributed State** - Faust Tables chia sẻ tự động  
✅ **Error Handling** - DLQ + exponential backoff  
✅ **Real-time Metrics** - Aggregation từ multiple workers  
✅ **Fault Tolerance** - Auto-rebalancing khi worker die  
✅ **Scaling** - Multiple workers xử lý cùng lúc  

---

## 🚀 GO NOW!

```bash
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust
pip install -r requirements.txt
docker-compose up -d

# Chạy Demo 3 (fastest)
python -m faust -A feature2_metrics worker -l info         # Terminal 1
python -m faust -A feature2_metrics worker -l info --web-port 6067  # Terminal 2
python producer.py -n 50 -i 0.5                            # Terminal 3

# Browser: http://localhost:6066/dashboard
```

✅ **Xong! 🎉**
