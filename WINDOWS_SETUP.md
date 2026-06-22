# Windows Setup Guide

Nếu bạn dùng Windows, hãy làm theo các bước sau:

## 1. Cài đặt Python Dependencies

```cmd
pip install -r requirements.txt
```

## 2. Khởi động Kafka qua Docker

```cmd
docker-compose up -d
```

Kiểm tra:
```cmd
docker ps
```

Nên thấy 2 containers chạy: `faust-kafka` và `faust-zookeeper`

## 3. Chạy App cơ bản

**Command Prompt 1:**
```cmd
faust -A app_base worker -l info
```

**Command Prompt 2:**
```cmd
faust -A app_base worker -l info --web-port 6067
```

**Command Prompt 3:**
```cmd
python producer.py -n 15 -i 0.8
```

## 4. Chạy Feature 1 (DLQ)

Dừng các command trước (Ctrl+C)

**Command Prompt 1:**
```cmd
faust -A feature1_dlq worker -l info
```

**Command Prompt 2:**
```cmd
faust -A feature1_dlq worker -l info --web-port 6067
```

**Command Prompt 3:**
```cmd
python producer.py -n 20 -i 1.5 -f 0.4
```

## 5. Chạy Feature 2 (Metrics Dashboard)

**Command Prompt 1:**
```cmd
faust -A feature2_metrics worker -l info
```

**Command Prompt 2:**
```cmd
faust -A feature2_metrics worker -l info --web-port 6067
```

**Command Prompt 3:**
```cmd
python producer.py -n 50 -i 0.5
```

**Browser:**
```
http://localhost:6066/dashboard
```

## 6. Dừng Kafka

```cmd
docker-compose down
```

## Troubleshooting

### Port đã dùng?
```cmd
netstat -ano | findstr :6066
taskkill /PID <PID> /F
```

### Kafka không chạy?
```cmd
docker-compose logs kafka
docker-compose restart
```

### Lỗi module?
```cmd
pip install --upgrade faust-streaming
```
