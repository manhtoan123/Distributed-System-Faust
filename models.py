# models.py
import faust


class Order(faust.Record, serializer='json'):
    """
    Đơn hàng — có thêm trường retry để phục vụ Tính năng 1.
    Faust Record tự động serialize/deserialize JSON qua Kafka.
    """
    order_id    : str
    user_id     : str
    product     : str
    quantity    : int
    price       : float
    retry_count : int = 0       # Số lần đã retry
    error_message: str = ''     # Lý do thất bại gần nhất
