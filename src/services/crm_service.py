from datetime import datetime, timedelta
from supabase import Client
import json

class CRMService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_upcoming_events(self, telegram_id: str) -> str:
        """
        Fetches birthdays/anniversaries within 7 days.
        Returns formatted text for the Relations Agent.
        """
        try:
            # 1. Get Profile ID
            res = self.supabase.table("profiles").select("id").eq("telegram_id", telegram_id).execute()
            if not res.data:
                return "User profile not found."
            profile_id = res.data[0]['id']

            # 2. Get All Contacts
            # MVP: Fetch all and filter in Python. Optimization: Use DB function later.
            contacts_res = self.supabase.table("contacts").select("*").eq("profile_id", profile_id).execute()
            if not contacts_res.data:
                return "Không có dữ liệu liên hệ (Contacts list is empty)."

            events = []
            today = datetime.now()
            next_week = today + timedelta(days=7)

            for contact in contacts_res.data:
                # Check Birthday
                if contact.get('birthday'):
                    bday_date = datetime.strptime(contact['birthday'], "%Y-%m-%d")
                    # Replace year with current year to check date
                    this_year_bday = bday_date.replace(year=today.year)
                    
                    # Handle year wrap-around (e.g. Dec 31 -> Jan 1) if needed, 
                    # but for simple 7-day lookahead, let's just check raw delta if within same year
                    # or handle the edge case where today is Dec 28 and bday is Jan 2.
                    
                    # Better logic:
                    # Calculate days until next birthday
                    dummy_bday = bday_date.replace(year=today.year)
                    if dummy_bday < today.replace(hour=0, minute=0, second=0, microsecond=0):
                        dummy_bday = dummy_bday.replace(year=today.year + 1)
                    
                    delta_days = (dummy_bday - today).days + 1 # +1 because delta starts at 0 for "tomorrow"? simple math: date - today
                    
                    # Using exact date comparison
                    if 0 <= (dummy_bday.date() - today.date()).days <= 7:
                        days_left = (dummy_bday.date() - today.date()).days
                        events.append({
                            "type": "Sinh nhật",
                            "name": contact['name'],
                            "days_left": days_left,
                            "date": dummy_bday.strftime("%d/%m"),
                            "prefs": contact.get('preferences', {})
                        })

                # Check Anniversary (Same logic)
                if contact.get('anniversary'):
                    ann_date = datetime.strptime(contact['anniversary'], "%Y-%m-%d")
                    dummy_ann = ann_date.replace(year=today.year)
                    if dummy_ann < today.replace(hour=0, minute=0, second=0, microsecond=0):
                        dummy_ann = dummy_ann.replace(year=today.year + 1)
                        
                    if 0 <= (dummy_ann.date() - today.date()).days <= 7:
                        days_left = (dummy_ann.date() - today.date()).days
                        events.append({
                            "type": "Kỷ niệm",
                            "name": contact['name'],
                            "days_left": days_left,
                            "date": dummy_ann.strftime("%d/%m"),
                            "prefs": contact.get('preferences', {})
                        })

            if not events:
                return "Không có sự kiện quan trọng nào trong 7 ngày tới."

            # Format Output
            output = "Danh sách sự kiện sắp tới:\n"
            for ev in events:
                urgency = "[URGENT] HÔM NAY!" if ev['days_left'] == 0 else f"Còn {ev['days_left']} ngày"
                prefs_str = ", ".join(ev['prefs'].get('wishlist', [])) if ev['prefs'].get('wishlist') else "Không có wishlist"
                output += f"- {ev['type']} {ev['name']} ({ev['date']}): {urgency}. Prefs: {prefs_str}\n"

            return output
            
        except Exception as e:
            return f"Error fetching CRM data: {str(e)}"
