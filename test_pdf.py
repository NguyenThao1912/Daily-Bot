from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from src.services.report.pdf_service import PDFService

def generate_dummy_chart(name, color):
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    path = os.path.join(output_dir, f"chart_{name}.png")
    
    fig = Figure(figsize=(10, 5))
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    
    ax.plot([1, 2, 3, 4, 5], [10, 25, 15, 30, 45], marker='o', color=color, linewidth=2)
    ax.set_title(f"Sample Chart: {name}")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    canvas.print_png(path)
    return path

def main():
    print("🚀 Generating Mock Data...")
    
    # 1. Mock Charts
    chart_finance = generate_dummy_chart("finance", "#27ae60")
    chart_weather = generate_dummy_chart("weather", "#2980b9")
    
    # 2. Mock Content (Rich HTML)
    results = [
        {
            "category": "finance",
            "content": """
            <div class="card">
                <div class="item-title">📈 THỊ TRƯỜNG CHỨNG KHOÁN</div>
                <table>
                    <thead>
                        <tr><th>Chỉ số</th><th>Điểm</th><th>Thay đổi</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>VN-INDEX</td><td>1,234.56</td><td><span style="color:green">+12.3 (1.0%)</span></td></tr>
                        <tr><td>HNX-INDEX</td><td>234.56</td><td><span style="color:red">-1.2 (0.5%)</span></td></tr>
                    </tbody>
                </table>
                <p>Thị trường mở cửa hứng khởi với dòng tiền lan tỏa. Nhóm Ngân hàng đóng vai trò dẫn dắt.</p>
                <div class="alert">💡 Hành động: Canh mua rung lắc tại vùng 1230.</div>
            </div>
            <div class="card">
                <div class="item-title">🏦 LÃI SUẤT & TỶ GIÁ</div>
                <ul>
                    <li>USD/VND: 24,500 (+10 đồng)</li>
                    <li>Lãi suất 12M (Big 4): 4.8% (Ổn định)</li>
                </ul>
            </div>
            """
        },
        {
            "category": "weather",
            "content": """
            <div class="card">
                <div class="item-title">🌤️ THỜI TIẾT HÔM NAY</div>
                <p><b>Hà Nội:</b> Có mây, ngày nắng. Nhiệt độ 25-32°C.</p>
                <p><b>TP.HCM:</b> Chiều tối có mưa rào. Nhiệt độ 26-34°C.</p>
                <div class="alert">☔ Lưu ý: Mang theo dù khi ra ngoài vào buổi chiều tại Sài Gòn.</div>
            </div>
            """
        },
        {
            "category": "news",
            "content": """
            <div class="card">
                <div class="item-title">📰 TIN TỨC ĐÁNG CHÚ Ý</div>
                <ul>
                    <li>Chính phủ phê duyệt quy hoạch điện 8 điều chỉnh.</li>
                    <li>Giá vàng thế giới vượt mốc 2400 USD/oz.</li>
                    <li>Apple ra mắt iPhone 16 với tính năng AI đột phá.</li>
                </ul>
            </div>
            """
        }
    ]
    
    chart_map = {
        "finance": chart_finance,
        "weather": chart_weather
    }
    
    # 3. Generate PDF
    print("⏳ Rendering PDF...")
    pdf_path = PDFService.generate_report(results, chart_map)
    
    if pdf_path:
        print(f"✅ Success! PDF created at: {pdf_path}")
    else:
        print("❌ PDF Generation Failed.")

if __name__ == "__main__":
    main()
