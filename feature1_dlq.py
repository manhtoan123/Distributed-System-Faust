# feature1_dlq.py
"""
Tính năng 1: Dead Letter Queue (DLQ) + Exponential Backoff Retry
================================================================
Luồng xử lý:
  1. main_processor nhận order từ 'orders' topic
  2. Nếu thất bại: retry_count++, gửi sang 'orders_retry' với delay 2^n giây
  3. Nếu vượt MAX_RETRIES: gửi sang 'orders_dlq' (Dead Letter Queue)
  4. dlq_monitor ghi log, cảnh báo (thực tế: gửi email/Slack)

Tính phân tán: dlq_stats là Faust Table — chia sẻ qua tất cả workers
"""
import asyncio
import random
from datetime import datetime

import faust
from models import Order

MAX_RETRIES  = 3
BACKOFF_BASE = 2   # Thời gian chờ = BACKOFF_BASE ^ retry_count (giây)

app = faust.App(
    'faust-dlq',
    broker='kafka://localhost:9092',
    value_serializer='json',
)

# ── Topics ───────────────────────────────────────────────────
orders_topic = app.topic('orders',       value_type=Order)
retry_topic  = app.topic('orders_retry', value_type=Order)
dlq_topic    = app.topic('orders_dlq',  value_type=Order)

# ── Distributed Statistics Table ─────────────────────────────
# Tất cả workers đều đọc/ghi bảng này qua Kafka changelog
dlq_stats = app.Table('dlq_stats', default=int)
# keys dùng: 'total', 'success', 'retry_sent', 'dlq'


# ── Hàm xử lý nghiệp vụ (có thể thất bại) ───────────────────
async def process_order_business_logic(order: Order) -> None:
    """
    Mô phỏng xử lý đơn hàng thực tế:
    - Gọi API thanh toán, cập nhật kho, v.v.
    - Order có 'FAIL' trong ID → luôn thất bại (để test)
    - 40% random failure để demo retry
    """
    if 'FAIL' in order.order_id:
        raise ValueError(f"Sai định dạng order: {order.order_id}")

    if random.random() < 0.40:
        raise ConnectionError("Dịch vụ thanh toán tạm thời không khả dụng")

    await asyncio.sleep(0.05)   # Simulate I/O


def ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


# ── Main Processor Agent ──────────────────────────────────────
@app.agent(orders_topic)
async def main_processor(stream):
    """Xử lý đơn hàng đến từ topic chính"""
    async for order in stream:
        dlq_stats['total'] += 1
        try:
            await process_order_business_logic(order)
            dlq_stats['success'] += 1
            print(f"[{ts()}] ✅ OK    {order.order_id} — {order.product}")

        except Exception as exc:
            order.retry_count  += 1
            order.error_message = str(exc)

            if order.retry_count <= MAX_RETRIES:
                delay = BACKOFF_BASE ** order.retry_count
                print(
                    f"[{ts()}] ⚠️  FAIL  {order.order_id} "
                    f"(lần {order.retry_count}/{MAX_RETRIES}): {exc}\n"
                    f"         → Retry sau {delay}s..."
                )
                dlq_stats['retry_sent'] += 1
                # Exponential backoff — await không block event loop
                await asyncio.sleep(delay)
                await retry_topic.send(value=order)
            else:
                dlq_stats['dlq'] += 1
                print(f"[{ts()}] ❌ DLQ   {order.order_id} hết lần retry")
                await dlq_topic.send(value=order)


# ── Retry Processor Agent ─────────────────────────────────────
@app.agent(retry_topic)
async def retry_processor(stream):
    """Xử lý lại các message đã thất bại"""
    async for order in stream:
        try:
            await process_order_business_logic(order)
            dlq_stats['success'] += 1
            print(
                f"[{ts()}] ✅ RETRY OK  {order.order_id} "
                f"(sau {order.retry_count} lần thử)"
            )

        except Exception as exc:
            order.retry_count  += 1
            order.error_message = str(exc)

            if order.retry_count <= MAX_RETRIES:
                delay = BACKOFF_BASE ** order.retry_count
                print(
                    f"[{ts()}] 🔄 RETRY {order.retry_count}/{MAX_RETRIES} "
                    f"thất bại cho {order.order_id}. Thử lại sau {delay}s"
                )
                dlq_stats['retry_sent'] += 1
                await asyncio.sleep(delay)
                await retry_topic.send(value=order)
            else:
                dlq_stats['dlq'] += 1
                print(f"[{ts()}] ❌ DLQ   {order.order_id} — chuyển vào DLQ")
                await dlq_topic.send(value=order)


# ── Dead Letter Queue Monitor ─────────────────────────────────
@app.agent(dlq_topic)
async def dlq_monitor(stream):
    """
    Xử lý message trong DLQ.
    Trong thực tế: gửi email alert, lưu DB để admin xem xét thủ công.
    """
    async for order in stream:
        print(f"\n{'='*55}")
        print(f"  🚨 DLQ ALERT — {ts()}")
        print(f"  Order ID    : {order.order_id}")
        print(f"  User        : {order.user_id}")
        print(f"  Sản phẩm   : {order.product} x{order.quantity}")
        print(f"  Lỗi cuối   : {order.error_message}")
        print(f"  Đã retry   : {order.retry_count} lần")
        print(f"  Hành động  : Cần xử lý thủ công!")
        print(f"{'='*55}\n")


# ── Báo cáo định kỳ (timer chạy trên mọi worker) ─────────────
@app.timer(interval=30.0)
async def periodic_report():
    total   = dlq_stats['total']
    success = dlq_stats['success']
    dlq     = dlq_stats['dlq']
    rate    = (success / total * 100) if total > 0 else 0

    print(f"\n[{ts()}] 📊 Báo cáo DLQ:")
    print(f"  Nhận tổng    : {total}")
    print(f"  Thành công   : {success}  ({rate:.1f}%)")
    print(f"  Retry đã gửi : {dlq_stats['retry_sent']}")
    print(f"  Vào DLQ      : {dlq}\n")


if __name__ == '__main__':
    app.main()
