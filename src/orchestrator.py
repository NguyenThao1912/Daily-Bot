import asyncio
import google.generativeai as genai
from datetime import datetime
from typing import List, Dict

class CategoryAgent:
    def __init__(self, name: str, api_key: str, system_prompt: str):
        self.name = name
        self.api_key = api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_impact(self, user_context: str, raw_data: str) -> str:
        full_prompt = f"{self.system_prompt}\n\nUSER PROFILE:\n{user_context}\n\nRAW DATA:\n{raw_data}"
        return await self.safe_generate(full_prompt)

    async def safe_generate(self, prompt: str, max_retries=3) -> str:
        import time
        from google.api_core import exceptions
        
        for i in range(max_retries):
            try:
                # Add delay to respect 15 RPM limit (4s per call safe for sequential, 
                # but for parallel execution in orchestrator we rely on semaphore or just simple logic)
                # Since orchestrator uses asyncio.gather, we should stagger or limit concurrency.
                # For now, strict 4s delay if we are hitting limits, but let's try just exception handling first 
                # + a small preemptive delay if running in loop.
                response = await asyncio.to_thread(self.model.generate_content, prompt)
                return response.text
            except exceptions.ResourceExhausted:
                wait_time = 10 * (i + 1)
                print(f"⚠️ Rate Limit hit for {self.name}. Waiting {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                return f"Error in {self.name} agent: {str(e)}"
        
        return f"❌ {self.name} Failed after retries (Rate Limit)."

class Orchestrator:
    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.agents: List[CategoryAgent] = []

    def add_agent(self, agent: CategoryAgent):
        self.agents.append(agent)

    async def run_all(self, user_context: str, category_data: Dict[str, str]) -> str:
        tasks = []
        import time
        results = []
        # Run sequentially to strictly respect RPM and avoid complex Semaphore logic for this Free Tier usage.
        # 15 RPM = 4 seconds per request.
        
        print(f"🚀 Starting AI Pipeline (Sequential Mode for Free Tier Compliance)...")
        
        for agent in self.agents:
            raw_data = category_data.get(agent.name, "No data available.")
            
            # Execute
            res = await agent.generate_impact(user_context, raw_data)
            results.append(res)
            
            # Sleep to respect 15 RPM
            print(f"💤 Sleeping 4s after {agent.name}...")
            await asyncio.sleep(4)
        
        # results = await asyncio.gather(*tasks) # Disabled for Free Tier Safety
        
        # Combine into a final report
        final_report = "🌅 *BẢN TIN CHIẾN LƯỢC (V3)*\n"
        final_report += f"*{datetime.now().strftime('%d/%m/%Y')} | High Impact Mode*\n"
        final_report += "\n".join(results)
        
        # Logic to extract alerts from Telegram Slash Commands
        self.alerts = self.extract_alerts(final_report)
        
        return final_report

    def extract_alerts(self, content: str) -> List[Dict]:
        """Looks for Telegram Slash Commands: /remind_keyword_HHhMM"""
        import re
        alerts = []
        # Regex to catch: /remind_uniqlo_10h00 or /remind_hop_10:30
        regex = r"\/remind_(\w+)_(\d{1,2})[h:](\d{2})"
        matches = re.findall(regex, content)
        
        for keyword, hour, minute in matches:
            time_str = f"{hour}:{minute}"
            title = f"Nhắc nhở: {keyword.replace('_', ' ').title()}"
            alerts.append({"title": title, "time": time_str})
            
        return alerts
