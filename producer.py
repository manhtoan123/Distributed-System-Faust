# producer.py
"""
Gửi đơn hàng thử nghiệm vào Kafka topic 'orders'.
Dùng --fail-rate để kiểm thử tính năng DLQ.
"""
import argparse
import json
import random
import time
import uuid

from kafka import KafkaProducer

PRODUCTS = ['Laptop', 'Phone', 'Tablet', 'Watch', 'Headphones', 'Keyboard']
USERS    = [f'user_{i}' for i in range(1, 6)]


def run(n: int = 20, interval: float = 1.0, fail_rate: float = 0.2):
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    )
    print(f"Gửi {n} đơn hàng | fail_rate={fail_rate*100:.0f}% | interval={interval}s\n")

    for i in range(n):
        is_fail  = random.random() < fail_rate
        prefix   = 'FAIL' if is_fail else 'ORD'
        order = {
            'order_id'    : f"{prefix}-{uuid.uuid4().hex[:8].upper()}",
            'user_id'     : random.choice(USERS),
            'product'     : random.choice(PRODUCTS),
            'quantity'    : random.randint(1, 5),
            'price'       : round(random.uniform(99.0, 1999.0), 2),
            'retry_count' : 0,
            'error_message': '',
        }
        producer.send('orders', value=order)
        icon = '💀' if is_fail else '📦'
        print(f"[{i+1:3}/{n}] {icon} {order['order_id']} | {order['product']}")
        time.sleep(interval)

    producer.flush()
    print(f"\n✅ Đã gửi {n} orders vào topic 'orders'")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n',  '--num',       type=int,   default=20,  help='Số orders')
    parser.add_argument('-i',  '--interval',  type=float, default=1.0, help='Giây/order')
    parser.add_argument('-f',  '--fail-rate', type=float, default=0.2, help='Tỷ lệ lỗi 0-1')
    args = parser.parse_args()
    run(args.num, args.interval, args.fail_rate)
