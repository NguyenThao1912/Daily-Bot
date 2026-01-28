import asyncio
import re
from datetime import datetime
from typing import List, Dict

# Thư viện mới (google-genai)
from google import genai
from google.genai import errors

class CategoryAgent:
    def __init__(self, name: str, api_key: str, system_prompt: str):
        self.name = name
        self.api_key = api_key
        self.system_prompt = system_prompt
        
        # Khởi tạo Client chuẩn (Bỏ http_options để SDK tự xử lý)
        self.client = genai.Client(api_key=self.api_key)

    async def generate_impact(self, user_context: str, raw_data: str) -> str:
        # Prompt Engineering: Ép khuôn output
        full_prompt = (
            f"{self.system_prompt}\n\n"
            f"--- USER CONTEXT ---\n{user_context}\n\n"
            f"--- REAL-TIME DATA ---\n{raw_data}\n\n"
            "YÊU CẦU: Chỉ trả về nội dung Impact và Action, ngắn gọn."
        )
        return await self.safe_generate(full_prompt)

    async def safe_generate(self, prompt: str, max_retries=3) -> str:
        # Cấu hình Model chuẩn
        # MODEL_NAME = 'gemini-2.0-flash-lite-preview-02-05' # Nếu muốn dùng bản 2.0 mới nhất
        MODEL_NAME = 'gemini-2.5-flash-lite' # Khuyên dùng bản này cho ổn định (Free Tier)

        for i in range(max_retries):
            try:
                # Dùng asyncio.to_thread để không chặn luồng chính
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=MODEL_NAME,
                    contents=prompt
                )
                return response.text
                
            except errors.ClientError as e:
                error_msg = str(e)
                # Xử lý Rate Limit (Lỗi 429)
                if "429" in error_msg or "ResourceExhausted" in error_msg:
                    wait_time = 5 * (i + 1) # Tăng dần thời gian chờ: 5s, 10s, 15s
                    print(f"⚠️ {self.name} bị Rate Limit. Chờ {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    return f"⚠️ Lỗi Agent {self.name}: {error_msg}"
            except Exception as e:
                return f"⚠️ Lỗi hệ thống {self.name}: {str(e)}"
        
        return f"❌ {self.name}: Bỏ qua do quá tải (Rate Limit)."

class Orchestrator:
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.agents: List[CategoryAgent] = []
        self.alerts = []

    def add_agent(self, agent: CategoryAgent):
        self.agents.append(agent)

    async def run_all(self, user_context: str, category_data: Dict[str, str]) -> str:
        results = []
        
        print(f"🚀 Bắt đầu chạy AI Pipeline (Chế độ Tuần tự - Safe Mode)...")
        
        for agent in self.agents:
            raw_data = category_data.get(agent.name, "Không có dữ liệu mới.")
            
            # 1. Thực thi Agent
            print(f"🤖 Đang chạy: {agent.name}...")
            res = await agent.generate_impact(user_context, raw_data)
            results.append(res)
            
            # 2. Nghỉ giữa các hiệp (Quan trọng cho Free Tier)
            # Gemini Flash giới hạn 15 RPM (4s/request). 
            # Nghỉ 4s là an toàn tuyệt đối.
            print(f"💤 Nghỉ 4s để hồi mana...")
            await asyncio.sleep(4)
        
        # Tổng hợp báo cáo
        current_date = datetime.now().strftime('%d/%m/%Y')
        final_report = f"🌅 *BẢN TIN CHIẾN LƯỢC (V3)*\n"
        final_report += f"*{current_date} | High Impact Mode*\n"
        final_report += "--------------------------------\n"
        final_report += "\n\n".join(results)
        
        # Trích xuất Alert từ báo cáo vừa tạo
        self.alerts = self.extract_alerts(final_report)
        
        return final_report

    def extract_alerts(self, content: str) -> List[Dict]:
        """
        Tìm lệnh dạng: /remind_keyword_10h30 hoặc /remind_keyword_10:30
        Hỗ trợ bắt keyword tiếng Việt không dấu.
        """
        alerts = []
        # Regex giải thích:
        # \/remind_ : Bắt đầu bằng /remind_
        # ([a-zA-Z0-9_]+) : Keyword (nên viết liền hoặc gạch dưới)
        # _(\d{1,2}) : Giờ
        # [h:] : Phân cách giờ phút (h hoặc :)
        # (\d{2}) : Phút
        regex = r"\/remind_([a-zA-Z0-9_]+)_(\d{1,2})[h:](\d{2})"
        
        matches = re.findall(regex, content)
        
        for keyword, hour, minute in matches:
            # Chuẩn hóa keyword (bỏ gạch dưới cho đẹp)
            clean_keyword = keyword.replace('_', ' ').title()
            time_str = f"{hour}:{minute}"
            
            alerts.append({
                "title": f"Nhắc nhở: {clean_keyword}",
                "time": time_str,
                "raw_cmd": f"/remind_{keyword}_{hour}h{minute}"
            })
            
        return alerts