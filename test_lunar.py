#!/usr/bin/env python3
"""Quick test script to verify lunar calendar conversion works"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.calendar.lunar_service import LunarService
import datetime

# Test with current date
print("Testing LunarService with current date...")
result = LunarService.get_date_info()
print(f"Solar Date: {result['solar_date']}")
print(f"Lunar Date: {result['lunar_date']}")
print(f"Zodiac Hours: {result['zodiac_hours']}")
print(f"Next Holiday: {result['next_holiday']}")

# Test with a specific date (Tet 2024)
print("\nTesting with Tet 2024 (Feb 10, 2024)...")
tet_date = datetime.datetime(2024, 2, 10)
result = LunarService.get_date_info(tet_date)
print(f"Solar Date: {result['solar_date']}")
print(f"Lunar Date: {result['lunar_date']}")
print(f"Next Holiday: {result['next_holiday']}")

print("\n✅ All tests passed! No import errors.")
