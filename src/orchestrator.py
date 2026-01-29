import asyncio
import re
from datetime import datetime
from typing import List, Dict

# Thư viện mới (google-genai)
from google import genai
from google.genai import errors, types

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
        MODEL_NAME = 'gemini-2.5-flash' # Khuyên dùng bản này cho ổn định (Free Tier)

        for i in range(max_retries):
            try:
                # Dùng asyncio.to_thread để không chặn luồng chính
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=MODEL_NAME,
                    contents=types.Part.from_text(text=prompt),
                    config={
                        'temperature': 0,
                        'top_p': 0.95,
                        'top_k': 20,
                    }
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

    async def run_all(self, user_context: str, category_data: Dict[str, str]) -> List[Dict[str, str]]:
        results = []
        processed_categories = set()
        
        print(f"🚀 Bắt đầu chạy AI Pipeline (Chế độ Song Song - Turbo Mode)...")
        
        # Limit concurrency to 3 agents at a time to avoid Rate Limit (429)
        semaphore = asyncio.Semaphore(3)

        # Helper function for individual agent task
        async def process_agent(agent):
            async with semaphore:
                raw_data = category_data.get(agent.name, "Không có dữ liệu mới.")
                processed_categories.add(agent.name)
                print(f"🤖 Start: {agent.name}...")
                try:
                    # Timeout after 45 seconds per agent
                    content = await asyncio.wait_for(agent.generate_impact(user_context, raw_data), timeout=45.0)
                    print(f"✅ Finish: {agent.name}")
                    return {"category": agent.name, "content": content}
                except asyncio.TimeoutError:
                    print(f"❌ Timeout ({agent.name}): Skipping...")
                    return {"category": agent.name, "content": f"⚠️ {agent.name}: Bỏ qua do AI treo quá lâu (>45s)."}
                except Exception as e:
                    print(f"❌ Error ({agent.name}): {e}")
                    return {"category": agent.name, "content": f"⚠️ {agent.name}: Lỗi xử lý ({str(e)})."}

        # Create tasks for all agents
        tasks = [process_agent(agent) for agent in self.agents]
        
        # Run concurrently (but bounded by Semaphore)
        results = await asyncio.gather(*tasks)

        # CLEANUP: Strip Markdown Code Blocks
        for res in results:
            content = res.get("content", "")
            if "```html" in content:
                res["content"] = content.replace("```html", "").replace("```", "").strip()
            elif "```" in content:
                res["content"] = content.replace("```", "").strip()
        
        # 3. (Deleted) Raw Data fallback removed as requested.
        
        # Extract Alerts from all results for persistence
        all_text = "\n\n".join([r["content"] for r in results])
        self.alerts = self.extract_alerts(all_text)
        
        return results

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