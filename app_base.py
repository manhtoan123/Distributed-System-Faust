"""
app_base.py — Demo cơ bản Faust
================================
Minh họa 3 khái niệm cốt lõi của Faust:
  1. Topic — kênh truyền dữ liệu (tương ứng Kafka topic)
  2. Agent — consumer/processor chạy liên tục dưới dạng async
  3. Table — bảng phân tán, lưu state chung giữa các worker

Chạy:
  Terminal 1: faust -A app_base worker -l info
  Terminal 2: faust -A app_base worker -l info --web-port 6067
  Terminal 3: python producer.py -n 15 -i 0.8
"""
import faust
from datetime import datetime
from models import Order


app = faust.App(
    'faust-base',
    broker='kafka://localhost:9092',
    value_serializer='json',
)

# ── Topic ────────────────────────────────────────────────────
orders_topic = app.topic('orders', value_type=Order)

# ── Distributed Tables (chia sẻ state qua Kafka changelog) ────
order_count_by_user = app.Table('base_order_count_by_user', default=int)
total_revenue = app.Table('base_total_revenue', default=float)
product_stats = app.Table('base_product_stats', default=dict)


def ts() -> str:
    """Timestamp cho log"""
    return datetime.now().strftime('%H:%M:%S')


# ── Main Agent ───────────────────────────────────────────────
@app.agent(orders_topic)
async def process_orders(stream):
    """
    Agent = coroutine async chạy mãi, đọc từng message từ stream.
    
    Khi chạy nhiều worker, Kafka tự chia partition cho từng worker.
    Tuy nhiên TẤT CẢ workers đều có quyền đọc/ghi Faust Tables
    (thông qua Kafka changelog topic), nên data luôn nhất quán.
    """
    async for order in stream:
        revenue = order.price * order.quantity

        # Cập nhật distributed tables
        order_count_by_user[order.user_id] += 1
        total_revenue['all'] += revenue

        # Cập nhật stats theo sản phẩm
        if order.product not in product_stats:
            product_stats[order.product] = {'count': 0, 'revenue': 0.0}
        stats = product_stats[order.product]
        stats['count'] += 1
        stats['revenue'] += revenue

        total_orders = sum(order_count_by_user.values())

        print(
            f"[{ts()}] ✅ [{order.order_id}] {order.product} x{order.quantity}"
            f" = ${revenue:.2f} | User {order.user_id} — "
            f"Tổng đơn: {int(total_orders)}"
        )


@app.timer(interval=15.0)
async def periodic_summary():
    """Báo cáo tổng hợp định kỳ"""
    total_users = len(order_count_by_user)
    total_orders = sum(order_count_by_user.values())
    total_rev = total_revenue.get('all', 0)

    print(f"\n[{ts()}] ═══ TÓNG HỢP (App Base) ═══")
    print(f"  Người dùng: {total_users}")
    print(f"  Tổng đơn: {int(total_orders)}")
    print(f"  Tổng doanh thu: ${float(total_rev):.2f}")

    if product_stats:
        print(f"  Top sản phẩm:")
        for prod, stats in sorted(product_stats.items(), key=lambda x: x[1]['revenue'], reverse=True)[:3]:
            print(f"    - {prod}: {stats['count']} đơn, ${stats['revenue']:.2f}")
    print()


if __name__ == '__main__':
    app.main()
