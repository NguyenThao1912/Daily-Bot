import json
from supabase import Client
from src.core.config import Config

class UserService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_user_context(self, telegram_id: str) -> str:
        """
        Fetches user profile from Supabase and formats it as an RPG Character Sheet.
        If no profile found, returns a default template.
        """
        try:
            response = self.supabase.table("profiles").select("*").eq("telegram_id", telegram_id).execute()
            if not response.data:
                return "User profile not found. Please set up your RPG profile."
            
            p = response.data[0]
            
            # Helper to parse JSONB safely
            inventory = p.get('inventory') or {}
            equipment = p.get('equipment') or {}
            traits = p.get('traits') or {}
            personal_goals = p.get('personal_goals') or {}

            # Format Assets
            assets_str = ""
            if inventory.get('investments'):
                for k, v in inventory['investments'].items():
                    assets_str += f"  - *{k}*: {v}\n"
            
            # Format Goals
            long_term = personal_goals.get('long_term', 'Tự do tài chính')
            short_term = "\n".join([f"- {q}" for q in personal_goals.get('short_term', [])])
            routines = "\n".join([f"- {q}" for q in personal_goals.get('routines', [])])

            context = f"""
# 👤 HỒ SƠ CÔNG DÂN (Citizen Profile)

## 1. THÔNG TIN CÁ NHÂN
- **Họ tên/Vai trò**: {p.get('full_name', 'Citizen')} - {p.get('role', 'Professional')}
- **Thâm niên**: {p.get('seniority', 'Experienced')}
- **Tình trạng sức khỏe**:
  - *Thể chất*: {p.get('physical_health', 'Normal')}
  - *Tinh thần*: {p.get('mental_state', 'Stable')}
- **Quỹ thời gian**: {p.get('available_time', 'Limited')}

## 2. TÌNH HÌNH TÀI CHÍNH
### 💰 Tài sản
- **Tiền mặt**: {p.get('cash_on_hand', 0):,} VND
- **Quỹ dự phòng**: {p.get('safety_fund', 0):,} VND
- **Danh mục đầu tư**:
{assets_str}

### 📊 Thu nhập & Hạ tầng
- **Nguồn thu chính**: {equipment.get('main_hand', 'Salary')}
- **Phương tiện**: {equipment.get('mount', 'Public Transport')}

## 3. ĐẶC ĐIỂM HÀNH VI
- **Phong cách**: {traits.get('alignment', 'Rational')}
- **Điểm mạnh**: {', '.join(traits.get('buffs', []))}
- **Điểm yếu**: {', '.join(traits.get('debuffs', []))}

## 4. MỤC TIÊU & KẾ HOẠCH
### 🎯 Mục tiêu dài hạn
- {long_term}

### ⚡ Ưu tiên ngắn hạn
{short_term}

### 🔄 Lịch trình cố định
{routines}
"""
            return context.strip()
        except Exception as e:
            return f"Error fetching profile: {str(e)}"
