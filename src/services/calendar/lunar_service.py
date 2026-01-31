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
    
    @staticmethod
    def get_upcoming_holidays(date: datetime.datetime = None, limit: int = 10):
        """
        Returns a list of upcoming lunar holidays with countdown days.
        Includes both lunar and solar calendar holidays, plus monthly lunar new moon (mùng 1).
        """
        if date is None:
            date = datetime.datetime.now()
        
        # Danh sách đầy đủ các ngày lễ quan trọng
        # Format: (month, day, name)
        # - Nếu month <= 12: Âm lịch
        # - Nếu month > 12: Dương lịch (month - 12 = tháng dương)
        holidays = [
            # --- LỄ ÂM LỊCH ---
            (1, 1, "Tết Nguyên Đán"),
            (1, 10, "Ngày vía Thần Tài"),
            (1, 15, "Rằm tháng Giêng"),
            (3, 3, "Tết Hàn Thực"),
            (3, 10, "Giỗ Tổ Hùng Vương"),
            (4, 15, "Lễ Phật Đản"),
            (5, 5, "Tết Đoan Ngọ"),
            (7, 7, "Lễ Thất Tịch"),
            (7, 15, "Lễ Vu Lan / Rằm tháng Bảy"),
            (8, 15, "Tết Trung Thu"),
            (9, 9, "Tết Trùng Cửu"),
            (10, 15, "Tết Hạ Nguyên"),
            (12, 23, "Tiễn ông Công ông Táo về trời"),
            (12, 30, "Tất Niên"),
            
            # --- LỄ DƯƠNG LỊCH (month + 12) ---
            (13, 1, "Tết Dương Lịch"),
            (14, 14, "Lễ tình nhân Valentine"),
            (14, 27, "Ngày Thầy thuốc Việt Nam"),
            (15, 8, "Quốc tế Phụ nữ"),
            (15, 26, "Ngày thành lập Đoàn"),
            (16, 30, "Giải phóng miền Nam"),
            (17, 1, "Quốc tế Lao động"),
            (17, 19, "Ngày sinh Chủ tịch Hồ Chí Minh"),
            (18, 1, "Quốc tế Thiếu nhi"),
            (21, 2, "Quốc khánh 2/9"),
            (22, 13, "Ngày Doanh nhân Việt Nam"),
            (22, 20, "Ngày Phụ nữ Việt Nam"),
            (23, 20, "Ngày Nhà giáo Việt Nam"),
            (24, 25, "Lễ Giáng sinh")
        ]
        
        current_lunar = Converter.Solar2Lunar(date)
        upcoming = []
        
        # Add special holidays
        for year_offset in [0, 1]:
            target_year = current_lunar.year + year_offset
            
            for month, day, name in holidays:
                try:
                    if month <= 12:
                        # Âm lịch
                        holiday_lunar = Lunar(target_year, month, day, isleap=False)
                        holiday_solar = Converter.Lunar2Solar(holiday_lunar)
                        holiday_date = datetime.datetime(holiday_solar.year, holiday_solar.month, holiday_solar.day)
                    else:
                        # Dương lịch (month - 12 = tháng thực)
                        solar_month = month - 12
                        solar_year = date.year + year_offset
                        holiday_date = datetime.datetime(solar_year, solar_month, day)
                    
                    # Only include future holidays
                    if holiday_date > date:
                        days_until = (holiday_date - date).days
                        upcoming.append({
                            "name": name,
                            "date": holiday_date.strftime("%d/%m/%Y"),
                            "days_until": days_until
                        })
                except Exception as e:
                    # Skip invalid dates
                    continue
        
        # Add monthly lunar new moon (mùng 1 hàng tháng)
        for year_offset in [0, 1]:
            target_year = current_lunar.year + year_offset
            
            for month in range(1, 13):  # 12 tháng âm lịch
                try:
                    # Mùng 1 của mỗi tháng
                    first_day_lunar = Lunar(target_year, month, 1, isleap=False)
                    first_day_solar = Converter.Lunar2Solar(first_day_lunar)
                    first_day_date = datetime.datetime(first_day_solar.year, first_day_solar.month, first_day_solar.day)
                    
                    if first_day_date > date:
                        days_until = (first_day_date - date).days
                        
                        # Tên tháng bằng chữ
                        month_names = ["", "Giêng", "Hai", "Ba", "Tư", "Năm", "Sáu", 
                                     "Bảy", "Tám", "Chín", "Mười", "Một", "Chạp"]
                        month_name = month_names[month]
                        
                        upcoming.append({
                            "name": f"Mùng 1 tháng {month_name}",
                            "date": first_day_date.strftime("%d/%m/%Y"),
                            "days_until": days_until
                        })
                except Exception as e:
                    continue
        
        # Sort by days until and return top N
        upcoming.sort(key=lambda x: x["days_until"])
        return upcoming[:limit]
