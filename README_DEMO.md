# 🎬 HƯỚNG DẪN DEMO CHI TIẾT - BẮNG ĐẦU NGAY

---

## ⚡ QUICK START (5 PHÚT ĐỂ START)

```bash
# Bước 1: Clone
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust

# Bước 2: Setup
pip install -r requirements.txt
docker-compose up -d

# Bước 3: Check
docker ps   # Nên thấy 2 containers
```

---

## 🎯 HƯỚNG DẪN CHI TIẾT - CHỌN MỘT TRONG:

### **📥 ĐỌC TRƯỚC TIÊN (Bắt buộc):**
→ File: **[CLONE_AND_DEMO.md](CLONE_AND_DEMO.md)** (10 phút)
- Cách clone từ GitHub
- Setup từng bước
- Chạy 4 demos với expected output
- Troubleshooting

### **🎬 CHI TIẾT TỪNG BƯỚC (Chuẩn bị demo):**
→ File: **[DEMO_GUIDE_VI.md](DEMO_GUIDE_VI.md)** (20 phút)
- Từng dòng output mong đợi
- Cách quan sát & giải thích
- Screenshot tips
- Kiểm tra checklist

### **🚀 BẮNG ĐẦU NGAY (Nếu muốn chạy ngay):**
→ File: **[START_DEMO_NOW.md](START_DEMO_NOW.md)** (3 phút)
- 3 lệnh setup
- Copy-paste ready commands
- 4 demos để chọn

---

## 📍 GITHUB REPOSITORY

**URL:** https://github.com/manhtoan123/Distributed-System-Faust

✅ **Đã push lên GitHub** - Sẵn sàng clone!

---

## 🎯 4 DEMOS AVAILABLE

| # | File | Output Expected | Time |
|---|------|-----------------|------|
| **1** | app_base.py | "Tổng đơn: 1 → 2 → 3 → ... → 15" | 15 min |
| **2** | feature1_dlq.py | Retry delays (2s, 4s, 8s) + DLQ alerts | 20 min |
| **3** | feature2_metrics.py | Dashboard + API JSON responses | 25 min |
| **4** | feature2_metrics.py (3 workers) | Rebalancing + metrics consistency | 15 min |

---

## 🔥 FASTEST DEMO (10 PHÚT - CHỈ DEMO 3)

```bash
# Terminal A
faust -A feature2_metrics worker -l info

# Terminal B
faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
python producer.py -n 50 -i 0.5

# Browser
http://localhost:6066/dashboard
```

✅ Sẽ thấy:
- 5 metric cards
- 3 charts (doughnut, bar, line)
- Auto-refresh
- Real-time updates

---

## 📊 KEY POINTS ĐỂ GIẢI THÍCH

### Demo 1 - Distributed State:
```
Worker A: Tổng đơn: 1, 3, 5, ...
Worker B: Tổng đơn: 2, 4, 6, ...
                ↓
          Nhưng cả 2 thấy: Tổng đơn: 15
          → Faust Table được chia sẻ!
```

### Demo 2 - Error Handling:
```
Message fail (retry 1) → chờ 2s
Message fail (retry 2) → chờ 4s
Message fail (retry 3) → chờ 8s
Message fail (retry > 3) → DLQ Alert
→ Exponential backoff works!
```

### Demo 3 - Metrics:
```
Worker 1: Xử lý message từ partition 0
Worker 2: Xử lý message từ partition 1
         → Nhưng metrics nhất quán!
         → Dashboard show aggregated view
```

### Demo 4 - Fault Tolerance:
```
3 workers chạy → Partition được chia 3 cách
Stop Worker 1 → Kafka rebalance → Workers 2,3 nhận extra partitions
Dashboard vẫn update (từ workers 2,3)
→ No message loss!
```

---

## 🛑 DỪNG (CLEANUP)

```bash
# Dừng workers: Ctrl+C ở mỗi terminal

# Dừng Kafka
docker-compose down

# Optional: Xóa data
docker-compose down -v
```

---

## ✅ CHECKLIST CHUẨN BỊ

- [ ] Repository cloned từ GitHub
- [ ] `pip install -r requirements.txt` (OK)
- [ ] `docker-compose up -d` (2 containers running)
- [ ] `docker ps` (faust-kafka, faust-zookeeper)
- [ ] `ls *.py` (5 Python files)
- [ ] Terminal windows: 3-4 cửa sổ mở sẵn
- [ ] Browser: Ready for http://localhost:6066/dashboard

---

## 📞 LỖI PHỔ BIẾN & FIX

### ❌ "Port 9092 already in use"
```bash
docker-compose down
docker-compose up -d
```

### ❌ "faust command not found"
```bash
pip install faust-streaming
```

### ❌ "Containers not running"
```bash
docker ps
docker-compose logs kafka
```

### ❌ "Producer connection refused"
```bash
# Kafka chưa ready, chờ 3-5 giây rồi thử lại
sleep 5
python producer.py -n 10
```

### ❌ "Dashboard not loading"
```bash
# Check if feature2_metrics app is running
curl http://localhost:6066/metrics/summary
```

---

## 🎬 DEMO FLOW (CHỌN 1 TRONG 3)

### **OPTION A: Full Demo (85 min)**
```
Setup (10) → Demo 1 (15) → Demo 2 (20) → Demo 3 (25) → Demo 4 (15)
```

### **OPTION B: Medium Demo (65 min)**
```
Setup (10) → Demo 1 (15) → Demo 3 (25) → Demo 4 (15)
```

### **OPTION C: Quick Demo (40 min)**
```
Setup (10) → Demo 3 (25) + explanation (5)
```

---

## 🎓 KỲ VỌNG SAU DEMO

Người xem sẽ hiểu:

✅ **Topics, Agents, Tables** của Faust  
✅ **Distributed State Sharing** (Faust Tables)  
✅ **Error Handling** (DLQ + Retry)  
✅ **Real-time Metrics** (Aggregation)  
✅ **Fault Tolerance** (Auto-rebalancing)  
✅ **Scaling** (Multiple workers)  

---

## 🚀 GÁY NGAY:

1. **Mở Terminal**
2. **`git clone https://github.com/manhtoan123/Distributed-System-Faust.git`**
3. **`cd Distributed-System-Faust`**
4. **`pip install -r requirements.txt`**
5. **`docker-compose up -d`**
6. **Đọc:** [CLONE_AND_DEMO.md](CLONE_AND_DEMO.md)
7. **Chạy Demo!** 🎬

---

## 📚 TÀI LIỆU

| File | Mục đích |
|------|---------|
| [CLONE_AND_DEMO.md](CLONE_AND_DEMO.md) | ⭐ **ĐỌC ĐẦU TIÊN** - Setup & Demos |
| [DEMO_GUIDE_VI.md](DEMO_GUIDE_VI.md) | Chi tiết từng step |
| [START_DEMO_NOW.md](START_DEMO_NOW.md) | Quick reference |
| [README.md](README.md) | Full documentation |
| [QUICK_START.md](QUICK_START.md) | 5-minute overview |

---

**⏱️ Thời gian:**
- Setup: 10 phút
- Demo 1 demos: 30 phút
- Giải thích: 10 phút
- **Total: 50 phút**

**💻 Yêu cầu:**
- Python 3.8+
- Docker
- 2 GB RAM (tối thiểu)

**✅ Status:** Sẵn sàng demo!

---

**Bắt đầu ngay! 🚀**
