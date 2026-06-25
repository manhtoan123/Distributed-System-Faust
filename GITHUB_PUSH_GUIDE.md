# 🚀 Hướng Dẫn Push Repo Lên GitHub

## ✅ Bước 1: Verify Repository đã tồn tại

```bash
cd Distributed-System-Faust
git remote -v
```

**Expected:**
```
origin  https://github.com/manhtoan123/Distributed-System-Faust.git (fetch)
origin  https://github.com/manhtoan123/Distributed-System-Faust.git (push)
```

---

## 📝 Bước 2: Check Status

```bash
git status
```

**Expected:**
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

✅ **Nếu thấy "nothing to commit"** → Repo đã sync, skip đến phần Demo

❌ **Nếu thấy "Untracked files" hoặc "Changes not staged"** → Làm tiếp bước 3

---

## 📤 Bước 3: Thêm tất cả file mới (nếu có)

```bash
git add .
git status
```

---

## 💬 Bước 4: Commit với message

```bash
git commit -m "Add complete Faust streaming project with 2 features and comprehensive documentation"
```

---

## 🔼 Bước 5: Push lên GitHub

```bash
git push origin main
```

**Expected:**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX), done.
Delta compression using up to 8 threads
...
To https://github.com/manhtoan123/Distributed-System-Faust.git
   abc1234..def5678  main -> main
```

✅ **Success!** Repository updated

---

## 🔍 Bước 6: Verify trên GitHub

1. Mở browser
2. Truy cập: https://github.com/manhtoan123/Distributed-System-Faust
3. Refresh page
4. Verify thấy tất cả files

---

## 🎯 Tiếp Theo: Clone & Demo

### Bước 7: Clone repository (để kiểm tra)

```bash
# Tạo thư mục demo
mkdir ~/demo
cd ~/demo

# Clone repo
git clone https://github.com/manhtoan123/Distributed-System-Faust.git
cd Distributed-System-Faust
```

### Bước 8: Setup & Run Demo

```bash
# Cài dependencies
pip install -r requirements.txt

# Khởi động Kafka
docker-compose up -d

# Verify Kafka
docker ps
```

### Bước 9: Chạy Demo 1 (3 Terminals)

**Terminal A:**
```bash
faust -A app_base worker -l info
```

**Terminal B:**
```bash
faust -A app_base worker -l info --web-port 6067
```

**Terminal C:**
```bash
python producer.py -n 15 -i 0.8
```

✅ Quan sát "Tổng đơn" tăng → Distributed state working!

---

## 📚 File Checklist

Verify tất cả file trong repo:

```bash
ls -1 | grep -E '\.(py|md|yml|txt|sh|json)$'
```

**Nên có:**
```
✅ .dockerignore
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
✅ STEP_BY_STEP.md
✅ FEATURES_DETAILED.md
✅ COMMANDS_REFERENCE.md
✅ PROJECT_SUMMARY.md
✅ WINDOWS_SETUP.md
✅ INDEX.md
✅ GRADING_GUIDE.md
✅ DELIVERY_SUMMARY.md
✅ FILE_LISTING.md
✅ DEMO_GUIDE_VI.md (Hướng dẫn demo này)
```

---

## 🎓 Summarize

| Bước | Lệnh | Output |
|------|------|--------|
| Check remote | `git remote -v` | Thấy origin URL |
| Check status | `git status` | clean hoặc Untracked |
| Add files | `git add .` | Staging changes |
| Commit | `git commit -m "..."` | Commit message |
| Push | `git push origin main` | Upload OK |
| Verify | Browser → GitHub | See all files |
| Clone | `git clone ...` | Local copy |
| Demo | `faust -A app_base ...` | See it work! |

---

✅ **Done! Repository is live on GitHub!**

Next → Follow [DEMO_GUIDE_VI.md](DEMO_GUIDE_VI.md) for detailed demo walkthrough
