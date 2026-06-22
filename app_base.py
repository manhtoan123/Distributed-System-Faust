# app_base.py
"""
Demo cơ bản: Hệ thống xử lý đơn hàng với Faust
================================================
Minh họa 3 khái niệm cốt lõi của Faust:
  1. Topic  — kênh truyền dữ liệu (tương ứng Kafka topic)
  2. Agent  — consumer/processor chạy liên tục dưới dạng async
  3. Table  — bảng phân tán, lưu state chung giữa các worker
"""
import faust
from models import Order

app = faust.App(
    'faust-base',                    # Tên app = Kafka consumer group ID
    broker='kafka://localhost:9092',
    value_serializer='json',
)

# ── Topic ────────────────────────────────────────────────────
orders_topic = app.topic('orders', value_type=Order)

# ── Table (phân tán, chia sẻ state qua Kafka changelog) ──────
order_count_by_user = app.Table('order_count_by_user', default=int)
total_revenue       = app.Table('total_revenue',       default=float)

# ── Agent ────────────────────────────────────────────────────
@app.agent(orders_topic)
async def process_orders(stream):
    """
    Agent = coroutine async chạy mãi, đọc từng message từ stream.
    Khi chạy nhiều worker, Kafka tự chia partition cho từng worker.
    """
    async for order in stream:
        revenue = order.price * order.quantity

        # Cập nhật distributed table — tất cả workers chia sẻ dữ liệu này
        order_count_by_user[order.user_id] += 1
        total_revenue['all']              += revenue

        print(
            f"✅ [{order.order_id}] {order.product} x{order.quantity}"
            f" = ${revenue:.2f} | User {order.user_id} "
            f"tổng {order_count_by_user[order.user_id]} đơn"
        )


if __name__ == '__main__':
    app.main()
