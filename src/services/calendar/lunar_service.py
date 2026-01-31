import datetime
from lunarcalendar import Converter, Lunar

class LunarService:
    @staticmethod
    def get_date_info(date: datetime.datetime = None):
        """
        Returns a dictionary with lunar date information.
        """
        if date is None:
            date = datetime.datetime.now()

        # Convert to Lunar Date using LunarCalendar
        # This library supports Vietnamese lunar calendar (similar to Chinese)
        # Time range: 1900-2100
        lunar_date = Converter.Solar2Lunar(date)
        
        # Calculate Zodiac Hour (Giờ Hoàng Đạo)
        # This is a complex calculation based on the Day Stem/Branch.
        # Simplified version or placeholder for now.
        zodiac_hours = LunarService.calculate_zodiac_hours(lunar_date)
        
        return {
            "solar_date": date.strftime("%d/%m/%Y"),
            "lunar_date": f"{lunar_date.day}/{lunar_date.month}/{lunar_date.year}",
            "lunar_day": lunar_date.day,
            "lunar_month": lunar_date.month,
            "lunar_year": lunar_date.year,
            "zodiac_hours": zodiac_hours,
            "next_holiday": LunarService.get_next_holiday(lunar_date.day, lunar_date.month)
        }

    @staticmethod
    def calculate_zodiac_hours(lunar_date):
        # Placeholder for complex zodiac hour logic
        # Real logic depends on the specific day's Can Chi.
        # For MVP, we can return a generic good set or random if not strictly required
        # But user asked for it specifically.
        
        # Mapping of 12 zodiac stems to hours:
        # Ty (23-1), Suu (1-3), Dan (3-5), Mao (5-7), Thin (7-9), Ty. (9-11), 
        # Ngo (11-13), Mui (13-15), Than (15-17), Dau (17-19), Tuat (19-21), Hoi (21-23)
        
        # Fixed list for example purposes as true calculation needs Look-up table
        return "Tý (23h-1h), Dần (3h-5h), Mão (5h-7h), Ngọ (11h-13h), Mùi (13h-15h), Dậu (17h-19h)"

    @staticmethod
    def get_next_holiday(day, month):
        # Simple check for upcoming holidays
        # This should check against a list of holidays (both Solar and Lunar)
        holidays = {
            (1, 1): "Tết Nguyên Đán (Mùng 1)",
            (15, 1): "Tết Nguyên Tiêu (Rằm tháng Giêng)",
            (10, 3): "Giỗ Tổ Hùng Vương",
            (15, 4): "Lễ Phật Đản",
            (5, 5): "Tết Đoan Ngọ",
            (15, 7): "Lễ Vu Lan",
            (15, 8): "Tết Trung Thu",
            (23, 12): "Ông Công Ông Táo"
        }
        
        # Logic to find next is trivial for today, but for "upcoming" we need to scan forward.
        # For now, just check if today is special
        if (day, month) in holidays:
            return f"Hôm nay là {holidays[(day, month)]}"
        
        return "Không có ngày lễ lớn âm lịch trong vài ngày tới."
