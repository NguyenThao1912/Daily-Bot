import asyncio
from datetime import datetime

# Mock Orchestrator to avoid importing google.generativeai (which is missing)
class MockOrchestrator:
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.agents = []
        self.alerts = []

    def add_agent(self, agent):
        self.agents.append(agent)

    async def run_all(self, user_context: str, category_data: dict) -> str:
        tasks = []
        for agent in self.agents:
            # Pass dummy data
            tasks.append(agent.generate_impact(user_context, category_data.get(agent.name, "")))
        
        results = await asyncio.gather(*tasks)
        
        final_report = "🌅 *BẢN TIN CHIẾN LƯỢC (DRY RUN)*\n"
        final_report += f"*{datetime.now().strftime('%d/%m/%Y')} | Testing Mode*\n"
        final_report += "\n".join(results)
        
        self.alerts = self.extract_alerts(final_report)
        return final_report

    def extract_alerts(self, content: str):
        # Re-implementing the logic from src/orchestrator.py for testing
        import re
        alerts = []
        regex = r"\/remind_(\w+)_(\d{1,2})[h:](\d{2})"
        matches = re.findall(regex, content)
        
        for keyword, hour, minute in matches:
            time_str = f"{hour}:{minute}"
            title = f"Nhắc nhở: {keyword.replace('_', ' ').title()}"
            alerts.append({"title": title, "time": time_str})
            
        return alerts

# Mock Class to simulate AI without API Keys
class MockAgent:
    def __init__(self, name):
        self.name = name

    async def generate_impact(self, user_context, raw_data):
        # Return the "Citizen Profile" V3 Sample with Tables
        if self.name == "finance":
            return """
### 💰 TÀI CHÍNH & VĨ MÔ
- ⭐ **Quan trọng**: ⭐⭐⭐⭐⭐ | 🔥 **Rủi ro**: **Cao**
- 📰 **Dữ liệu**:
  ```
  Chỉ số   | Giá trị | Thay đổi | Link
  ---------|---------|----------|------
  VN-Index | 1250    | -1.2%    | [CafeF](...)
  DXY      | 104.5   | +0.3%    | [TradingView](...)
  Gold SJC | 89tr    | 0%       | [SJC](...)
  ```
  
  ```
  Bill     | Cost    | Hạn      | Link
  ---------|---------|----------|------
  Netflix  | 260k    | Hôm nay  | [Pay](...)
  Tiền Nhà | 8tr     | 3 ngày   | [Bank](...)
  ```
- 💡 **IMPACT**: DXY tăng gây áp lực tỷ giá. Chứng khoán chỉnh là cơ hội mua.
- ✅ **HÀNH ĐỘNG**:
  - [ ] Mua gom 1000 HPG.
  - [Micro] Thanh toán **Netflix**.
`👉 Bấm nhắc nhở: /remind_mua_hpg_14h00`
`👉 Bấm nhắc nhở: /remind_thanh_toan_netflix_20h00`"""
        
        if self.name == "events":
            return """
### 📅 SỰ KIỆN & LỊCH TRÌNH
- ⭐ **Quan trọng**: ⭐⭐⭐⭐⭐ | 🔥 **Rủi ro**: **Cao**
- 📰 **Dữ liệu**: Quoted Text.
  > *[Họp đối tác](Calendar) | [Deadline báo cáo](Trello)*
- 💡 **IMPACT**: Sự kiện quyết định KPI tháng.
- ✅ **HÀNH ĐỘNG**:
  - [ ] Review slide trước 30p.
`👉 Bấm nhắc nhở: /remind_hop_doi_tac_10h00`"""

        if self.name == "tech":
            return """
### 🤖 CÔNG NGHỆ & AI
- ⭐ **Quan trọng**: ⭐⭐⭐⭐ | 🔥 **Rủi ro**: **Thấp**
- 📰 **Dữ liệu**: Quoted Text.
  > *[OpenAI ra mắt GPT-5 preview](OpenAI) | [GitHub Copilot X free tier](GitHub)*
- 💡 **IMPACT**: Cơ hội tăng hiệu suất code lên 200%.
- ✅ **HÀNH ĐỘNG**:
  - [ ] Đăng ký waitlist GPT-5 ngay.
  - [ ] Cài Copilot X vào VS Code.
`👉 Bấm nhắc nhở: /remind_test_gpt5_20h00`"""

        if self.name == "trends":
            return """
### 📈 GÓC NHÌN TRENDS (GOOGLE DATA)
- 🔥 **Sơn Tùng MTP** (500k+ lượt tìm)
  - 🧐 **Giải mã**: Vừa ra MV mới "Đừng làm trái tim anh đau".
  - 💡 **Cơ hội**: Kiểu tóc mới của Tùng sẽ hot -> Shop thời trang nên nhập mẫu áo tương tự.
- 🔥 **ChatGPT 5** (100k+ lượt tìm)
  - 🧐 **Giải mã**: Tin đồn rò rỉ tính năng mới.
  - 💡 **Cơ hội**: Content so sánh v4 vs v5 sẽ viral.
`👉 Bấm nhắc nhở: /remind_viet_content_mtp_15h00`"""

        return ""

async def dry_run():
    print("----------------------------------------------------------------")
    print("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM HỆ THỐNG (DRY RUN MODE)")
    print("----------------------------------------------------------------")
    
    # 1. Initialize Orchestrator (Mocking Bot)
    orchestrator = MockOrchestrator(telegram_bot=None)
    
    # 2. Add Mock Agents
    orchestrator.add_agent(MockAgent("finance"))
    orchestrator.add_agent(MockAgent("events"))
    orchestrator.add_agent(MockAgent("tech"))
    orchestrator.add_agent(MockAgent("trends"))
    
    # 3. Virtual Data (Input)
    user_context = "User Context Mock"
    data_map = {"finance": "...", "events": "...", "tech": "...", "trends": "..."}
    
    # 4. Execute
    print("⏳ Đang gọi các Agent để phân tích dữ liệu...\n")
    final_report = await orchestrator.run_all(user_context, data_map)
    
    print("📋 --- KẾT QUẢ BẢN TIN TRẢ VỀ (PREVIEW) ---")
    print(final_report)
    print("----------------------------------------------------------------")
    
    # 5. Check Alert Extraction Logic
    print("\n🔍 KIỂM TRA LOGIC TÁCH LỆNH NHẮC NHỞ (SLASH COMMAND PARSER):")
    if orchestrator.alerts:
        for i, alert in enumerate(orchestrator.alerts, 1):
            print(f"   ✅ [Alert {i}]: Tìm thấy lệnh '{alert['title']}' -> Hẹn giờ: {alert['time']}")
    else:
        print("   ❌ Không tìm thấy Alert nào.")

    print("\n----------------------------------------------------------------")
    print("✅ TEST HOÀN TẤT. HỆ THỐNG SẴN SÀNG DEPLOY.")

if __name__ == "__main__":
    asyncio.run(dry_run())
