"""
producer.py — Gửi đơn hàng thử nghiệm vào Kafka topic 'orders'
==============================================================
Dùng để test các Faust app với dữ liệu giả lập.

Ví dụ:
  python producer.py -n 20 -i 1.0 -f 0.2     # 20 đơn, 1 giây/đơn, 20% fail
  python producer.py -n 50 -i 0.5            # 50 đơn, 0.5 giây/đơn
"""
import argparse
import json
import random
import time
import uuid

from kafka import KafkaProducer

PRODUCTS = ['Laptop', 'Phone', 'Tablet', 'Watch', 'Headphones', 'Keyboard', 'Monitor']
USERS = [f'user_{i}' for i in range(1, 6)]


def run(n: int = 20, interval: float = 1.0, fail_rate: float = 0.2):
    """
    Args:
        n: Số đơn hàng gửi
        interval: Thời gian (giây) giữa các đơn
        fail_rate: Tỷ lệ đơn có 'FAIL' prefix để test retry (0-1)
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=5000,
        )
    except Exception as e:
        print(f"❌ Không thể kết nối Kafka: {e}")
        print("Hãy chạy: docker-compose up -d")
        return

    print(f"\n📤 Gửi {n} đơn hàng")
    print(f"   Interval: {interval}s | Fail rate: {fail_rate*100:.0f}%\n")

    for i in range(n):
        is_fail = random.random() < fail_rate
        prefix = 'FAIL' if is_fail else 'ORD'
        order = {
            'order_id': f"{prefix}-{uuid.uuid4().hex[:8].upper()}",
            'user_id': random.choice(USERS),
            'product': random.choice(PRODUCTS),
            'quantity': random.randint(1, 5),
            'price': round(random.uniform(99.0, 1999.0), 2),
            'retry_count': 0,
            'error_message': '',
        }

        try:
            producer.send('orders', value=order)
            icon = '💀' if is_fail else '📦'
            print(
                f"[{i+1:3}/{n}] {icon} {order['order_id']} | "
                f"{order['product']} x{order['quantity']} = ${order['price']*order['quantity']:.2f}"
            )
            time.sleep(interval)
        except Exception as e:
            print(f"❌ Lỗi gửi order: {e}")

    producer.flush()
    print(f"\n✅ Đã gửi {n} orders vào topic 'orders'\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Producer gửi test orders vào Kafka'
    )
    parser.add_argument(
        '-n', '--num',
        type=int,
        default=20,
        help='Số đơn hàng (default: 20)'
    )
    parser.add_argument(
        '-i', '--interval',
        type=float,
        default=1.0,
        help='Giây/đơn (default: 1.0)'
    )
    parser.add_argument(
        '-f', '--fail-rate',
        type=float,
        default=0.2,
        help='Tỷ lệ lỗi 0-1 (default: 0.2)'
    )
    args = parser.parse_args()

    if not (0 <= args.fail_rate <= 1):
        print("❌ --fail-rate phải từ 0 đến 1")
        exit(1)

    run(args.num, args.interval, args.fail_rate)
