import os
import sys
from datetime import datetime

# Add src to path to import PDFService
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.report.pdf_service import PDFService

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

def generate_dummy_charts(output_dir="output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    charts = {}
    
    # helper for OO plotting
    def save_chart(fig, filename):
        path = os.path.join(output_dir, filename)
        FigureCanvas(fig).print_png(path)
        return path

    # 1. Trend Chart
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(111)
    ax.barh(['Trend A', 'Trend B', 'Trend C', 'Trend D', 'Trend E'], [50000, 40000, 30000, 20000, 10000], color='#3498db')
    ax.set_title("Top Google Trends (Mock)")
    charts['TRENDS'] = [save_chart(fig, "mock_trend.png")]

    # 2. Finance Charts (Multiple)
    # Foreign Flow
    fig = Figure(figsize=(8, 5))
    ax = fig.add_subplot(111)
    ax.barh(['AAA', 'BBB', 'CCC', 'DDD', 'EEE'], [10, 5, 2, -3, -8], color=['g','g','g','r','r'])
    ax.set_title("Foreign Flow (Mock)")
    chart_path_ff = save_chart(fig, "mock_foreign.png")

    # Commodities
    fig = Figure(figsize=(8, 5))
    ax = fig.add_subplot(111)
    ax.barh(['Gold', 'Oil', 'BTC', 'Silver'], [0.5, -1.2, 2.3, 0.1], color=['g','r','g','g'])
    ax.set_title("Commodities (Mock)")
    chart_path_comm = save_chart(fig, "mock_comm.png")
    
    charts['FINANCE'] = [chart_path_ff, chart_path_comm]

    return charts

def main():
    print("🚀 Generating Mock Data for PDF Report...")
    
    # 1. Generate Dummy Charts
    chart_map = generate_dummy_charts()
    
    # 2. Mock HTML Content (Rich with Premium Style Classes)
    
    # --- FINANCE CONTENT ---
    finance_html = """
    <div class="card">
        <div class="item-title">💰 TÀI CHÍNH VĨ MÔ</div>
        <div class="item-meta">⭐ Đánh giá: 4/5 | 🔥 Rủi ro: Trung bình</div>
        
        <div class="item-content">
            <div class="sub-label">📉 Dữ liệu Vĩ mô:</div>
            <table>
                <tr><th>Chỉ số</th><th>Giá trị</th><th>Thay đổi</th></tr>
                <tr><td>DXY</td><td>104.5</td><td>+0.2%</td></tr>
                <tr><td>US10Y</td><td>4.2%</td><td>-0.1%</td></tr>
                <tr><td>VN-Index</td><td>1250.0</td><td>+5.4 pts</td></tr>
            </table>
        </div>

        <div class="alert">
            ℹ️ <b>Nhận định:</b> DXY tăng nhẹ gây áp lực tỷ giá, nhưng dòng tiền nội vẫn cân tốt.
        </div>

        <div class="item-content action-highlight">
            <div class="sub-label" style="color: #d35400;"><b>⚡ HÀNH ĐỘNG CẦN LÀM:</b></div>
            <ul>
                <li>[ ] Canh mua cổ phiếu KCN khi chỉnh đỏ (Quan trọng)</li>
                <li>[ ] Giảm tỷ trọng Margin nếu VNI thủng 1240</li>
            </ul>
        </div>
    </div>

    <div class="card">
        <div class="item-title">🏦 BANKING & RATE</div>
        <div class="item-content">
           <div class="sub-label">Tỷ giá bán VCB:</div>
           <p><b>25.450 VND/USD</b> (Ổn định)</p>
        </div>
    </div>
    """

    # --- NEWS TRENDS CONTENT ---
    trends_html = """
    <div class="card">
        <div class="item-title">🔥 GOOGLE TRENDS VIETNAM</div>
        <div class="item-content">
            <ul>
                <li><b>Sơn Tùng M-TP</b> (100k+ lượt): Ra mắt MV mới...</li>
                <li><b>Giá Vàng hôm nay</b> (50k+ lượt): Vàng nhẫn tăng vọt...</li>
                <li><b>Bão số 1</b> (20k+ lượt): Dự báo đổ bộ...</li>
            </ul>
        </div>
        <div class="alert">
            👉 Xu hướng giải trí đang chiếm sóng. Cẩn thận tin fake news về bão.
        </div>
    </div>
    """

    # --- WEATHER CONTENT ---
    weather_html = """
    <div class="card">
        <div class="item-title">🌤️ THỜI TIẾT HÀ NỘI</div>
        <div class="item-meta">Nhiệt độ: 25°C | Độ ẩm: 70%</div>
        <div class="item-content">
            <p>Trời nhiều mây, chiều tối có mưa rào rải rác. Đi đường cẩn thận trơn trượt.</p>
        </div>
        <div class="item-content action-highlight">
             <div class="sub-label" style="color: #d35400;"><b>⚡ HÀNH ĐỘNG:</b></div>
             <ul><li>[ ] Mang theo ô/áo mưa khi ra ngoài sau 5h chiều.</li></ul>
        </div>
    </div>
    """
    
    # 3. Assemble Results
    results = [
        {"category": "FINANCE", "content": finance_html},
        {"category": "TRENDS", "content": trends_html},
        {"category": "WEATHER", "content": weather_html}
    ]

    # 4. Generate PDF
    pdf_path = PDFService.generate_report(results, chart_map)
    
    if pdf_path:
        print(f"✅ Mock PDF generated successfully: {pdf_path}")
        # Automatically open on Mac
        os.system(f"open '{pdf_path}'")
    else:
        print("❌ Failed to generate PDF.")

if __name__ == "__main__":
    main()
