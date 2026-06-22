# feature2_metrics.py
"""
Tính năng 2: Distributed Real-time Metrics Dashboard
=====================================================
- Thu thập metrics từ stream qua Faust Agent
- Lưu vào Faust Table (phân tán, chia sẻ giữa các workers)
- Expose HTTP API:
    GET /metrics/summary    → tổng quan
    GET /metrics/users      → theo user
    GET /metrics/products   → theo sản phẩm
    GET /metrics/throughput → throughput theo phút
- Dashboard HTML tại http://localhost:6066/dashboard
  (tự refresh mỗi 5 giây, dùng Chart.js)
"""
from datetime import datetime

import faust
from aiohttp.web import Response, json_response
from models import Order

app = faust.App(
    'faust-metrics',
    broker='kafka://localhost:9092',
    value_serializer='json',
    web_host='0.0.0.0',
    web_port=6066,
)

orders_topic = app.topic('orders', value_type=Order)

# ── Distributed Metric Tables ─────────────────────────────────
global_stats    = app.Table('m_global',    default=float)
orders_by_user  = app.Table('m_by_user',  default=int)
revenue_by_prod = app.Table('m_by_prod',  default=float)
orders_by_prod  = app.Table('m_prod_cnt', default=int)
throughput      = app.Table('m_thru',     default=int)


# ── Metrics Collector Agent ───────────────────────────────────
@app.agent(orders_topic)
async def metrics_collector(stream):
    """
    Mỗi order đến, agent cập nhật tất cả bảng phân tán.
    Khi chạy nhiều worker, mỗi worker xử lý một phần partition —
    nhưng TẤT CẢ đều đọc/ghi cùng Faust Tables (via Kafka changelog).
    """
    async for order in stream:
        revenue = order.price * order.quantity
        minute  = datetime.now().strftime('%H:%M')

        global_stats['total_orders']  += 1
        global_stats['total_revenue'] += revenue

        orders_by_user[order.user_id] += 1

        revenue_by_prod[order.product] += revenue
        orders_by_prod[order.product]  += 1

        throughput[minute] += 1

        total = global_stats['total_orders']
        if total > 0:
            global_stats['avg_order_value'] = (
                global_stats['total_revenue'] / total
            )

        print(
            f"[METRICS] {order.order_id} | "
            f"{order.product} x{order.quantity} = ${revenue:.2f} | "
            f"Tổng đơn: {int(total)}"
        )


# ── HTTP API Endpoints ────────────────────────────────────────
@app.page('/metrics/summary')
async def api_summary(web, request):
    return json_response({
        'total_orders'   : int(global_stats['total_orders']),
        'total_revenue'  : round(float(global_stats['total_revenue']), 2),
        'avg_order_value': round(float(global_stats['avg_order_value']), 2),
        'timestamp'      : datetime.now().isoformat(),
    })


@app.page('/metrics/users')
async def api_users(web, request):
    return json_response({k: int(v) for k, v in orders_by_user.items()})


@app.page('/metrics/products')
async def api_products(web, request):
    products = {}
    for prod in set(list(orders_by_prod.keys()) + list(revenue_by_prod.keys())):
        products[prod] = {
            'orders' : int(orders_by_prod.get(prod, 0)),
            'revenue': round(float(revenue_by_prod.get(prod, 0)), 2),
        }
    return json_response(products)


@app.page('/metrics/throughput')
async def api_throughput(web, request):
    # Trả về 15 phút gần nhất, sắp xếp theo thời gian
    items = sorted(throughput.items())[-15:]
    return json_response(dict(items))


# ── HTML Dashboard ────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="">
<title>Faust Distributed Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:24px}
  h1{text-align:center;color:#7dd3fc;font-size:1.6rem;margin-bottom:4px}
  .sub{text-align:center;color:#64748b;font-size:.85rem;margin-bottom:28px}
  .status{text-align:right;font-size:.75rem;margin-bottom:20px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-bottom:28px}
  .card{background:#1e293b;border-radius:12px;padding:20px;border-left:4px solid #3b82f6}
  .card.g{border-left-color:#22c55e}.card.p{border-left-color:#a855f7}.card.o{border-left-color:#f97316}
  .lbl{font-size:.75rem;color:#94a3b8;margin-bottom:6px}
  .val{font-size:1.9rem;font-weight:700;color:#f1f5f9}
  .charts{display:grid;grid-template-columns:1fr 1fr;gap:20px}
  .box{background:#1e293b;border-radius:12px;padding:20px}
  .box h3{color:#7dd3fc;font-size:.8rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}
  canvas{max-height:240px}
  @media(max-width:700px){.charts{grid-template-columns:1fr}}
</style>
</head>
<body>
<h1>📊 Faust Distributed Stream Dashboard</h1>
<p class="sub">Real-time Metrics — Workers chia sẻ state qua Kafka Tables</p>
<div class="status" id="st">Đang kết nối...</div>

<div class="cards">
  <div class="card"><div class="lbl">📦 Tổng đơn hàng</div><div class="val" id="v1">—</div></div>
  <div class="card g"><div class="lbl">💰 Tổng doanh thu</div><div class="val" id="v2">—</div></div>
  <div class="card p"><div class="lbl">📈 Trung bình/đơn</div><div class="val" id="v3">—</div></div>
  <div class="card o"><div class="lbl">🛍️ Sản phẩm</div><div class="val" id="v4">—</div></div>
</div>

<div class="charts">
  <div class="box"><h3>Doanh thu theo sản phẩm</h3><canvas id="c1"></canvas></div>
  <div class="box"><h3>Đơn hàng theo user</h3><canvas id="c2"></canvas></div>
  <div class="box"><h3>Throughput (đơn/phút)</h3><canvas id="c3"></canvas></div>
</div>

<script>
const CLR=['#3b82f6','#22c55e','#f97316','#a855f7','#ef4444','#14b8a6','#eab308'];
const DARK={color:'#94a3b8'};
const GRID={color:'#334155'};
function mkChart(id,type,data){
  return new Chart(document.getElementById(id),{
    type,data,
    options:{
      responsive:true,
      plugins:{legend:{labels:DARK}},
      scales:type==='doughnut'?{}:{
        x:{ticks:DARK,grid:GRID},
        y:{ticks:DARK,grid:GRID}
      }
    }
  });
}
let c1,c2,c3;
async function load(){
  try{
    const[sum,users,prods,thru]=await Promise.all([
      fetch('/metrics/summary').then(r=>r.json()),
      fetch('/metrics/users').then(r=>r.json()),
      fetch('/metrics/products').then(r=>r.json()),
      fetch('/metrics/throughput').then(r=>r.json()),
    ]);
    document.getElementById('v1').textContent=sum.total_orders.toLocaleString();
    document.getElementById('v2').textContent='$'+sum.total_revenue.toLocaleString();
    document.getElementById('v3').textContent='$'+sum.avg_order_value.toFixed(0);
    document.getElementById('v4').textContent=Object.keys(prods).length;
    document.getElementById('st').innerHTML='🟢 Live — '+new Date().toLocaleTimeString();

    // Chart 1: Revenue by product (doughnut)
    const pl=Object.keys(prods), pv=pl.map(p=>prods[p].revenue);
    if(!c1) c1=mkChart('c1','doughnut',{labels:pl,datasets:[{data:pv,backgroundColor:CLR,borderWidth:0}]});
    else{c1.data.labels=pl;c1.data.datasets[0].data=pv;c1.update();}

    // Chart 2: Orders by user (bar)
    const ul=Object.keys(users), uv=ul.map(u=>users[u]);
    if(!c2) c2=mkChart('c2','bar',{labels:ul,datasets:[{label:'Đơn',data:uv,backgroundColor:'#3b82f6',borderRadius:5}]});
    else{c2.data.labels=ul;c2.data.datasets[0].data=uv;c2.update();}

    // Chart 3: Throughput (line)
    const tk=Object.keys(thru).slice(-12), tv=tk.map(k=>thru[k]);
    if(!c3) c3=mkChart('c3','line',{labels:tk,datasets:[{label:'Đơn/phút',data:tv,borderColor:'#22c55e',backgroundColor:'rgba(34,197,94,.1)',fill:true,tension:.4}]});
    else{c3.data.labels=tk;c3.data.datasets[0].data=tv;c3.update();}
  }catch{document.getElementById('st').innerHTML='🔴 Lỗi kết nối';}
}
load();
setInterval(load,5000);   // Auto-refresh 5 giây
</script>
</body></html>
"""

@app.page('/dashboard')
async def dashboard_page(web, request):
    return Response(text=DASHBOARD_HTML, content_type='text/html')


# ── Báo cáo console định kỳ ───────────────────────────────────
@app.timer(interval=20.0)
async def console_report():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ═══ METRICS REPORT ═══")
    print(f"  Tổng đơn  : {int(global_stats['total_orders'])}")
    print(f"  Doanh thu : ${float(global_stats['total_revenue']):.2f}")
    print(f"  Avg/đơn   : ${float(global_stats['avg_order_value']):.2f}")
    top = sorted(revenue_by_prod.items(), key=lambda x: x[1], reverse=True)[:3]
    for p, r in top:
        print(f"  Top prod  : {p} — ${r:.2f}")
    print()


if __name__ == '__main__':
    app.main()
