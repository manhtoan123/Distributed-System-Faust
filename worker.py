import faust

# Khởi tạo App Faust với web port 6099
app = faust.App(
    'hello-distributed-app', 
    broker='kafka://localhost:9092',
    value_serializer='json',
    web_port=6099,  
)

# Định nghĩa luồng (Topic) nhận tin nhắn
hello_topic = app.topic('hello-topic')

# Worker lắng nghe và xử lý dữ liệu realtime từ luồng
@app.agent(hello_topic)
async def process_greetings(greetings):
    async for greeting in greetings:
        print(f"✅ Faust Worker xử lý thành công: {greeting}")

if __name__ == '__main__':
    app.main()
