import sys
import os
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.services.calendar.lunar_service import LunarService
except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure you are running this from the project root or have installed requirements.")
    sys.exit(1)

def test_lunar_service():
    print("Testing LunarService...")
    try:
        data = LunarService.get_date_info()
        print("Received Data:")
        for k, v in data.items():
            print(f"  {k}: {v}")
        
        # assertions
        assert "lunar_date" in data
        assert "zodiac_hours" in data
        assert "next_holiday" in data
        print("\n✅ LunarService Test Passed!")
    except Exception as e:
        print(f"\n❌ LunarService Test Failed: {e}")

if __name__ == "__main__":
    test_lunar_service()
