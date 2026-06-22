# 🔧 Copy-Paste Commands Reference

Dùng file này để copy-paste các lệnh mà không cần gõ lại.

---

## ⚡ Setup Ban đầu (1 lần)

### Cài Dependencies
```bash
pip install -r requirements.txt
```

### Khởi động Kafka
```bash
docker-compose up -d
```

### Kiểm tra Kafka
```bash
docker ps
```

### Dừng Kafka (sau khi hoàn thành)
```bash
docker-compose down
```

---

## 🚀 App Cơ bản (Demo Topics, Agents, Tables)

### Worker 1
```bash
faust -A app_base worker -l info
```

### Worker 2 (tab/terminal khác)
```bash
faust -A app_base worker -l info --web-port 6067
```

### Producer (tab/terminal thứ 3)
```bash
python producer.py -n 15 -i 0.8
```

---

## 🛡️ Feature 1 — DLQ + Retry

### Worker 1
```bash
faust -A feature1_dlq worker -l info
```

### Worker 2
```bash
faust -A feature1_dlq worker -l info --web-port 6067
```

### Producer (40% fail-rate)
```bash
python producer.py -n 20 -i 1.5 -f 0.4
```

---

## 📊 Feature 2 — Metrics Dashboard

### Worker 1
```bash
faust -A feature2_metrics worker -l info
```

### Worker 2
```bash
faust -A feature2_metrics worker -l info --web-port 6067
```

### Producer
```bash
python producer.py -n 50 -i 0.5
```

### Dashboard (Browser)
```
http://localhost:6066/dashboard
```

### API Endpoints (Terminal)
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

## 🔄 Advanced: Multi-Worker (3 workers)

### Worker 1
```bash
faust -A feature2_metrics worker -l info
```

### Worker 2
```bash
faust -A feature2_metrics worker -l info --web-port 6067
```

### Worker 3
```bash
faust -A feature2_metrics worker -l info --web-port 6068
```

### Producer (more data)
```bash
python producer.py -n 100 -i 0.3
```

---

## 🐳 Docker Commands (Production)

### Build Image
```bash
docker build -t faust-app:latest .
```

### Run Single Container
```bash
docker run --rm --network host faust-app:latest \
    faust -A app_base worker -l info
```

### Verify Image Size
```bash
docker images | grep faust-app
```

### View Container Logs
```bash
docker logs faust-app
```

---

## 🔍 Troubleshooting Commands

### Verify Python
```bash
python --version
```

### Verify Faust
```bash
python -c "import faust; print(faust.__version__)"
```

### Test Kafka Connection
```bash
python -c "from kafka import KafkaProducer; \
producer = KafkaProducer(bootstrap_servers='localhost:9092'); \
print('✅ OK'); producer.close()"
```

### Check Docker Containers
```bash
docker ps
```

### Check Kafka Logs
```bash
docker-compose logs kafka
```

### Check Zookeeper
```bash
docker-compose logs zookeeper
```

### List Kafka Topics
```bash
docker exec faust-kafka kafka-topics \
    --bootstrap-server localhost:9092 \
    --list
```

### View Messages in Topic
```bash
docker exec faust-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic orders \
    --from-beginning \
    --max-messages 5
```

### Restart Kafka
```bash
docker-compose restart
```

### Remove All Containers (⚠️ Careful!)
```bash
docker-compose down -v
```

---

## 📝 Producer Variations

### Basic (20 orders, 1s gap, 0% fail)
```bash
python producer.py -n 20
```

### High Volume (100 orders, fast)
```bash
python producer.py -n 100 -i 0.2
```

### High Failure Rate (20 orders, 50% fail)
```bash
python producer.py -n 20 -i 2.0 -f 0.5
```

### Continuous (run multiple times)
```bash
for i in {1..5}; do
    python producer.py -n 20 -i 0.5
    sleep 5
done
```

---

## 🌐 Port Management

### Free Up Port (if already in use)
```bash
# Find process using port 6066
lsof -i :6066

# Kill process (macOS/Linux)
kill -9 <PID>

# Windows
netstat -ano | findstr :6066
taskkill /PID <PID> /F
```

### Alternative Ports for 2nd Worker
```bash
# If port 6067 is taken, use 6068
faust -A feature2_metrics worker -l info --web-port 6068

# Or 6069, 6070, etc.
```

---

## 📊 Pretty Print JSON APIs

### Using Python
```bash
curl http://localhost:6066/metrics/summary | python -m json.tool
```

### Using jq (if installed)
```bash
curl http://localhost:6066/metrics/summary | jq .
```

### Using grep (basic)
```bash
curl http://localhost:6066/metrics/summary | grep total_orders
```

---

## 🔐 Kill All Faust Workers

### macOS/Linux
```bash
pkill -f "faust -A"
```

### Windows (PowerShell)
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process
```

---

## 📤 Upload to Production

### Build and Push to Docker Hub
```bash
docker build -t yourname/faust-app:latest .
docker push yourname/faust-app:latest
```

### Deploy on Linux Server
```bash
ssh user@server
cd /opt/faust-app
git pull
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📚 View Logs Real-time

### Docker Compose
```bash
docker-compose logs -f kafka
docker-compose logs -f
```

### Single Container
```bash
docker logs -f <container_id>
```

### Terminal (Faust output)
```bash
# Redirect to file
faust -A feature2_metrics worker -l info > app.log 2>&1

# View
tail -f app.log
```

---

## 🧹 Cleanup

### Remove All Faust Containers
```bash
docker-compose down
```

### Remove All Data
```bash
docker-compose down -v
```

### Remove Image
```bash
docker rmi faust-app:latest
```

### Remove Containers & Images
```bash
docker-compose down && docker rmi faust-app:latest
```

---

## 📋 One-Liner Commands

### Full Setup (if running step-by-step)
```bash
pip install -r requirements.txt && docker-compose up -d && sleep 3 && echo "✅ Ready"
```

### Test Everything (after setup)
```bash
python -c "import faust; from kafka import KafkaProducer; print('✅ All imports OK')"
```

### Start Demo (3 terminals needed)
```bash
# Terminal 1
faust -A app_base worker -l info

# Terminal 2
faust -A app_base worker -l info --web-port 6067

# Terminal 3
python producer.py -n 15 -i 0.8
```

---

## 🛑 Emergency Stop

### Stop All (Ctrl+C không work)
```bash
# Kill all Python processes related to Faust
pkill -9 -f "faust"
pkill -9 -f "python.*producer"

# Stop Docker
docker-compose down -v
```

---

## ✅ Verification Checklist

### All systems go?
```bash
# 1. Check Python
python --version

# 2. Check Docker
docker-compose ps

# 3. Check Kafka
docker exec faust-kafka kafka-topics --bootstrap-server localhost:9092 --list | head -5

# 4. Check imports
python -c "import faust, kafka; print('✅')"
```

---

Copy-paste these commands dễ dàng!
