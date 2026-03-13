from datetime import datetime, timedelta
from supabase import Client

class SubscriptionService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_upcoming_bills(self, telegram_id: str) -> str:
        """
        Fetches subscriptions due within 7 days.
        Returns formatted text for Finance Agent.
        """
        try:
            # 1. Get Profile ID
            res = self.supabase.table("profiles").select("id").eq("telegram_id", telegram_id).execute()
            if not res.data:
                return "User profile not found."
            profile_id = res.data[0]['id']

            # 2. Get Subscriptions
            subs_res = self.supabase.table("subscriptions").select("*").eq("profile_id", profile_id).eq("status", "active").execute()
            if not subs_res.data:
                return "Không có hóa đơn định kỳ nào (No active subscriptions)."

            bills = []
            today = datetime.now()
            
            for sub in subs_res.data:
                due_date = datetime.strptime(sub['next_due_date'], "%Y-%m-%d")
                
                # Simple logic for now: exact date match or future within 7 days
                # In production, we'd handle 'recurring' logic update here or via Worker
                
                delta_days = (due_date.date() - today.date()).days
                
                if 0 <= delta_days <= 7:
                    bills.append({
                        "name": sub['name'],
                        "cost": sub['cost'],
                        "currency": sub.get('currency', 'VND'),
                        "days_left": delta_days,
                        "date": due_date.strftime("%d/%m")
                    })

            if not bills:
                return "✅ Tuần này không có hóa đơn nào đến hạn."

            # Format Output
            total_vnd = sum(b['cost'] for b in bills if b['currency'] == 'VND')
            output = f"💸 HÓA ĐƠN SẮP ĐẾN HẠN (Tổng: {total_vnd:,.0f} VND):\n"
            
            for b in bills:
                urgency = "[THANH TOÁN NGAY]" if b['days_left'] <= 1 else f"Còn {b['days_left']} ngày"
                cost_str = f"{b['cost']:,.0f} {b['currency']}"
                output += f"- {b['name']}: {cost_str}. Hạn: {b['date']} -> {urgency}\n"

            return output
            
        except Exception as e:
            return f"Error fetching subscriptions: {str(e)}"
