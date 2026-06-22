"""
models.py — Data Models dùng chung cho tất cả Faust apps
=========================================================
Faust Record tự động serialize/deserialize JSON qua Kafka.
"""
import faust


class Order(faust.Record, serializer='json'):
    """
    Đơn hàng — có thêm trường retry để phục vụ Tính năng 1 (DLQ).
    
    Attributes:
        order_id: Mã đơn hàng duy nhất (định dạng: ORD-xxxx hoặc FAIL-xxxx để test)
        user_id: ID người dùng
        product: Tên sản phẩm
        quantity: Số lượng đặt
        price: Giá đơn vị
        retry_count: Số lần đã retry (để track exponential backoff)
        error_message: Lỗi gần nhất nếu có
    """
    order_id: str
    user_id: str
    product: str
    quantity: int
    price: float
    retry_count: int = 0
    error_message: str = ''


class OrderEvent(faust.Record, serializer='json'):
    """
    Sự kiện liên quan đến đơn hàng — cho feature2 metrics tracking
    """
    event_type: str  # 'created', 'processed', 'failed', 'dlq'
    order_id: str
    user_id: str
    product: str
    revenue: float
    timestamp: str
