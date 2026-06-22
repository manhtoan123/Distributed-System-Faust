"""
feature2_metrics.py — Tính năng 2: Distributed Real-time Metrics Dashboard
===========================================================================
- Thu thập metrics từ stream qua Faust Agent
- Lưu vào Faust Table (phân tán, chia sẻ giữa các workers)
- Expose HTTP API:
    GET /metrics/summary    → tổng quan
    GET /metrics/users      → theo user
    GET /metrics/products   → theo sản phẩm
    GET /metrics/throughput → throughput theo phút
- Dashboard HTML tại http://localhost:6066/dashboard
  (tự refresh mỗi 5 giây, dùng Chart.js)

Chạy:
  Terminal 1: faust -A feature2_metrics worker -l info
  Terminal 2: faust -A feature2_metrics worker -l info --web-port 6067
  Terminal 3: python producer.py -n 50 -i 0.5
  
  Mở trình duyệt:
    - http://localhost:6066/dashboard         ← Dashboard
    - http://localhost:6066/metrics/summary   ← API JSON
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

orders_topic = app.topic('orders', value_type=Order, partitions=3)

# ── Distributed Metric Tables ─────────────────────────────────
global_stats = app.Table('m_global', default=float)
orders_by_user = app.Table('m_by_user', default=int)
revenue_by_prod = app.Table('m_by_prod', default=float)
orders_by_prod = app.Table('m_prod_cnt', default=int)
throughput = app.Table('m_thru', default=int)


def ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


# ── Metrics Collector Agent ───────────────────────────────────
@app.agent(orders_topic, concurrency=4)
async def metrics_collector(stream):
    """
    Mỗi order đến, agent cập nhật tất cả bảng phân tán.
    
    Khi chạy nhiều worker, mỗi worker xử lý một phần partition —
    nhưng TẤT CẢ đều đọc/ghi cùng Faust Tables (via Kafka changelog).
    Faust Table tự động handle conflict resolution & synchronization.
    """
    async for order in stream:
        revenue = order.price * order.quantity
        minute = datetime.now().strftime('%H:%M')

        global_stats['total_orders'] += 1
        global_stats['total_revenue'] += revenue

        orders_by_user[order.user_id] += 1

        revenue_by_prod[order.product] += revenue
        orders_by_prod[order.product] += 1

        throughput[minute] += 1

        total = global_stats['total_orders']
        if total > 0:
            global_stats['avg_order_value'] = (
                global_stats['total_revenue'] / total
            )

        print(
            f"[{ts()}] [METRICS] {order.order_id} | "
            f"{order.product} x{order.quantity} = ${revenue:.2f} | "
            f"Tổng đơn: {int(total)}"
        )


# ── HTTP API Endpoints ────────────────────────────────────────
@app.page('/metrics/summary')
async def api_summary(web, request):
    """Tóm tắt metrics chung"""
    return json_response({
        'total_orders': int(global_stats.get('total_orders', 0)),
        'total_revenue': round(float(global_stats.get('total_revenue', 0)), 2),
        'avg_order_value': round(float(global_stats.get('avg_order_value', 0)), 2),
        'timestamp': datetime.now().isoformat(),
    })


@app.page('/metrics/users')
async def api_users(web, request):
    """Thống kê đơn hàng theo user"""
    return json_response({k: int(v) for k, v in orders_by_user.items()})


@app.page('/metrics/products')
async def api_products(web, request):
    """Thống kê theo sản phẩm (số lượng + doanh thu)"""
    products = {}
    all_prods = set(list(orders_by_prod.keys()) + list(revenue_by_prod.keys()))
    for prod in all_prods:
        products[prod] = {
            'orders': int(orders_by_prod.get(prod, 0)),
            'revenue': round(float(revenue_by_prod.get(prod, 0)), 2),
        }
    return json_response(products)


@app.page('/metrics/throughput')
async def api_throughput(web, request):
    """Throughput theo phút (20 phút gần nhất)"""
    items = sorted(throughput.items())[-20:]
    return json_response(dict(items))


# ── HTML Dashboard ────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Faust Distributed Metrics Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{
    font-family:'Segoe UI','Roboto',sans-serif;
    background:linear-gradient(135deg,#0f172a 0%,#1a1f35 100%);
    color:#e2e8f0;
    padding:24px;
    min-height:100vh;
  }
  .container{max-width:1400px;margin:0 auto}
  h1{
    text-align:center;
    background:linear-gradient(135deg,#7dd3fc,#06b6d4);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    font-size:2rem;
    margin-bottom:4px;
    font-weight:700;
  }
  .sub{text-align:center;color:#64748b;font-size:.85rem;margin-bottom:8px}
  .status{text-align:right;font-size:.75rem;margin-bottom:20px;color:#22c55e}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-bottom:28px}
  .card{
    background:#1e293b;
    border-radius:12px;
    padding:20px;
    border-left:4px solid #3b82f6;
    transition:transform 0.2s;
  }
  .card:hover{transform:translateY(-2px)}
  .card.g{border-left-color:#22c55e}
  .card.p{border-left-color:#a855f7}
  .card.o{border-left-color:#f97316}
  .card.r{border-left-color:#ef4444}
  .lbl{font-size:.75rem;color:#94a3b8;margin-bottom:6px;text-transform:uppercase}
  .val{font-size:1.8rem;font-weight:700;color:#f1f5f9}
  .charts{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px}
  .box{background:#1e293b;border-radius:12px;padding:20px;border:1px solid #334155}
  .box h3{color:#7dd3fc;font-size:.8rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}
  canvas{max-height:260px}
  .full{grid-column:1/-1}
  @media(max-width:900px){.charts{grid-template-columns:1fr}}
  .footer{text-align:center;color:#64748b;font-size:.75rem;margin-top:20px}
</style>
</head>
<body>
<div class="container">
<h1>📊 Faust Distributed Metrics Dashboard</h1>
<p class="sub">Real-time Streaming Analytics — Multiple workers sharing state via Kafka Tables</p>
<div class="status" id="st">🟢 Connecting...</div>

<div class="cards">
  <div class="card"><div class="lbl">📦 Total Orders</div><div class="val" id="v1">—</div></div>
  <div class="card g"><div class="lbl">💰 Total Revenue</div><div class="val" id="v2">—</div></div>
  <div class="card p"><div class="lbl">📈 Avg per Order</div><div class="val" id="v3">—</div></div>
  <div class="card o"><div class="lbl">🛍️ Unique Products</div><div class="val" id="v4">—</div></div>
  <div class="card r"><div class="lbl">👥 Unique Users</div><div class="val" id="v5">—</div></div>
</div>

<div class="charts">
  <div class="box"><h3>💰 Revenue by Product</h3><canvas id="c1"></canvas></div>
  <div class="box"><h3>📦 Orders by User</h3><canvas id="c2"></canvas></div>
  <div class="box full"><h3>📈 Throughput (orders/minute, 20 min window)</h3><canvas id="c3"></canvas></div>
</div>

<div class="footer">Last update: <span id="lu">—</span> | Data refreshes every 5 seconds</div>
</div>

<script>
const CLR=['#3b82f6','#22c55e','#f97316','#a855f7','#ef4444','#14b8a6','#eab308','#ec4899'];
const DARK={color:'#94a3b8'};
const GRID={color:'#334155'};

function mkChart(id,type,data){
  return new Chart(document.getElementById(id),{
    type,data,
    options:{
      responsive:true,
      maintainAspectRatio:true,
      plugins:{
        legend:{labels:{...DARK,usePointStyle:true}}
      },
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
    document.getElementById('v2').textContent='$'+sum.total_revenue.toLocaleString('en-US',{maximumFractionDigits:0});
    document.getElementById('v3').textContent='$'+sum.avg_order_value.toFixed(0);
    document.getElementById('v4').textContent=Object.keys(prods).length;
    document.getElementById('v5').textContent=Object.keys(users).length;
    document.getElementById('lu').textContent=new Date().toLocaleTimeString();
    document.getElementById('st').innerHTML='🟢 Live — '+new Date().toLocaleTimeString();

    // Chart 1: Revenue by product (doughnut)
    const pl=Object.keys(prods).sort((a,b)=>prods[b].revenue-prods[a].revenue), 
          pv=pl.map(p=>prods[p].revenue);
    if(!c1) c1=mkChart('c1','doughnut',{
      labels:pl,
      datasets:[{data:pv,backgroundColor:CLR.slice(0,pl.length),borderWidth:2,borderColor:'#1e293b'}]
    });
    else{c1.data.labels=pl;c1.data.datasets[0].data=pv;c1.update();}

    // Chart 2: Orders by user (bar)
    const ul=Object.keys(users).sort((a,b)=>users[b]-users[a]), 
          uv=ul.map(u=>users[u]);
    if(!c2) c2=mkChart('c2','bar',{
      labels:ul,
      datasets:[{label:'Orders',data:uv,backgroundColor:'#3b82f6',borderRadius:6}]
    });
    else{c2.data.labels=ul;c2.data.datasets[0].data=uv;c2.update();}

    // Chart 3: Throughput (line)
    const tk=Object.keys(thru).slice(-15), 
          tv=tk.map(k=>thru[k]);
    if(!c3) c3=mkChart('c3','line',{
      labels:tk,
      datasets:[{
        label:'Orders/minute',
        data:tv,
        borderColor:'#22c55e',
        backgroundColor:'rgba(34,197,94,.1)',
        borderWidth:3,
        fill:true,
        tension:.4,
        pointBackgroundColor:'#22c55e',
        pointRadius:4
      }]
    });
    else{c3.data.labels=tk;c3.data.datasets[0].data=tv;c3.update();}
  }catch(e){
    console.error('Load error:',e);
    document.getElementById('st').innerHTML='🔴 Connection error';
  }
}

load();
setInterval(load,5000);  // Auto-refresh 5 giây
</script>
</body></html>
"""


@app.page('/dashboard')
async def dashboard_page(web, request):
    """Serve dashboard HTML"""
    return Response(text=DASHBOARD_HTML, content_type='text/html')


# ── Báo cáo console định kỳ ───────────────────────────────────
@app.timer(interval=25.0)
async def console_report():
    total = int(global_stats.get('total_orders', 0))
    revenue = float(global_stats.get('total_revenue', 0))
    avg = float(global_stats.get('avg_order_value', 0))

    print(f"\n[{ts()}] ═══ METRICS REPORT ═══")
    print(f"  Tổng đơn  : {total}")
    print(f"  Doanh thu : ${revenue:.2f}")
    print(f"  Avg/đơn   : ${avg:.2f}")

    if revenue_by_prod:
        top = sorted(revenue_by_prod.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  Top products:")
        for p, r in top:
            print(f"    • {p}: ${r:.2f}")
    print()


if __name__ == '__main__':
    app.main()
