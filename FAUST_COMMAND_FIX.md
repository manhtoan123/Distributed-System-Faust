# 🔧 FIX: "faust command not found" on Windows

## ✅ SOLUTION

Trên Windows PowerShell, `faust` command có thể không được tìm thấy. **Thay vì thế, dùng:**

```bash
python -m faust -A app_base worker -l info
```

---

## 📝 ÁP DỤNG CHO TẤT CẢ COMMANDS

### **Trước đây (Lỗi):**
```bash
faust -A app_base worker -l info
faust -A feature1_dlq worker -l info
faust -A feature2_metrics worker -l info
```

### **Bây giờ (OK):**
```bash
python -m faust -A app_base worker -l info
python -m faust -A feature1_dlq worker -l info
python -m faust -A feature2_metrics worker -l info
```

---

## 🎬 CHẠY DEMO CHÍNH XÁC

### **Demo 1: App Base**

```bash
# Terminal A
python -m faust -A app_base worker -l info

# Terminal B
python -m faust -A app_base worker -l info --web-port 6067

# Terminal C
python producer.py -n 15 -i 0.8
```

### **Demo 2: DLQ + Retry**

```bash
# Terminal A
python -m faust -A feature1_dlq worker -l info

# Terminal B
python -m faust -A feature1_dlq worker -l info --web-port 6067

# Terminal C (40% fail rate)
python producer.py -n 20 -i 1.5 -f 0.4
```

### **Demo 3: Metrics Dashboard (RECOMMENDED)**

```bash
# Terminal A
python -m faust -A feature2_metrics worker -l info

# Terminal B
python -m faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
python producer.py -n 50 -i 0.5

# Browser
http://localhost:6066/dashboard
```

### **Demo 4: Multi-Worker (3 workers)**

```bash
# Terminal A
python -m faust -A feature2_metrics worker -l info

# Terminal B
python -m faust -A feature2_metrics worker -l info --web-port 6067

# Terminal C
python -m faust -A feature2_metrics worker -l info --web-port 6068

# Terminal D
python producer.py -n 100 -i 0.2
```

---

## ✅ QUICK START (3 STEPS)

```bash
# 1. Setup
pip install -r requirements.txt
docker-compose up -d

# 2. Verify Kafka running
docker ps
# Should see: faust-kafka and faust-zookeeper

# 3. Run Demo 3 (fastest)
python -m faust -A feature2_metrics worker -l info      # Terminal 1
python -m faust -A feature2_metrics worker -l info --web-port 6067   # Terminal 2
python producer.py -n 50 -i 0.5                          # Terminal 3

# 4. View Dashboard
# Browser: http://localhost:6066/dashboard
```

---

## 📋 CHECKLIST

- [x] Dùng `python -m faust` thay vì `faust`
- [x] Tất cả demos sẽ work
- [x] Windows PowerShell compatible
- [x] No environment variable issues

---

**Ready to demo! 🚀**
