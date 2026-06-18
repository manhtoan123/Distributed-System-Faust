import faust

app = faust.App(
    'hello-distributed-app', 
    broker='kafka://localhost:9092',
    value_serializer='json',
    web_port=6080,  # Ép Faust chạy web server ở cổng 6080 tránh bị xung đột
)

hello_topic = app.topic('hello-topic')

@app.agent(hello_topic)
async def process_greetings(greetings):
    async for greeting in greetings:
        print(f"✅ Faust Worker nhận được tin nhắn từ Kafka: {greeting}")

@app.timer(interval=3.0)
async def send_greeting():
    message = f"Xin chào từ Toàn! (Mã sinh viên: 23010539)"
    await process_greetings.send(value=message)

if __name__ == '__main__':
    app.main()