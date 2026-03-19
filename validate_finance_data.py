import sys
import os
import time

# Add src to path
sys.path.append(os.getcwd())

# Mock Config if needed or ensure it doesn't crash
try:
    from src.config import Config
except:
    pass

from src.services.stock.stock_service import StockService
from src.services.finance.market_service import MarketService
from src.services.finance.banking_service import BankingService

def validate_api(name, func, *args):
    print(f"🔄 Testing {name}...", end=" ", flush=True)
    try:
        start = time.time()
        result = func(*args)
        duration = time.time() - start
        
        is_valid = False
        details = ""
        
        if result:
            if isinstance(result, list) and len(result) > 0:
                is_valid = True
                details = f"List[{len(result)}]"
            elif isinstance(result, dict) and bool(result):
                is_valid = True
                details = f"Dict keys: {list(result.keys())[:3]}..."
            elif isinstance(result, tuple) and any(result):
                is_valid = True
                details = f"Tuple len={len(result)}"
            elif isinstance(result, str) and len(result) > 0:
                 is_valid = True
                 details = f"String len={len(result)}"
        
        if is_valid:
            print(f"✅ OK ({duration:.2f}s) - {details}")
            return True
        else:
            print(f"❌ EMPTY/NULL ({duration:.2f}s)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

print("\n--- 🔍 VALIDATING FINANCE DATA APIs ---\n")

# 1. STOCK SERVICE
print("--- STOCK SERVICE ---")
all_records = StockService._fetch_all_records_sync()
if all_records:
    print(f"✅ cophieu68 download/process: OK ({len(all_records)} rows)")
    grouped = StockService._group_records_by_symbol(all_records)
    symbol = "HPG"
    hist = grouped.get(symbol, [])
    if hist:
        print(f"✅ grouped history ({symbol}): OK ({len(hist)} rows)")
        try:
            rsi, ma20, ma50, ma200, vol_avg = StockService.calculate_technical_indicators(hist)
            print(f"   👉 RSI: {rsi}")
            print(f"   👉 MA20: {ma20}")
            print(f"   👉 MA50: {ma50}")
            print(f"   👉 MA200: {ma200}")
            print(f"   👉 Vol20: {vol_avg}")
        except Exception as e:
            print(f"❌ calculate_technical_indicators: FAILED ({e})")
    else:
        print(f"❌ grouped history ({symbol}): FAILED/EMPTY")
else:
    print("❌ cophieu68 download/process: FAILED/EMPTY")

# Test main fetch string
print(" Testing Stock Output String:")
try:
    # Improve Robustness of test: Config might lack watchlist
    # Mocking Config.STOCK_WATCHLIST if empty
    from src.config import Config
    if not hasattr(Config, 'STOCK_WATCHLIST') or not Config.STOCK_WATCHLIST:
        Config.STOCK_WATCHLIST = ["HPG", "VCB", "FPT"]
        
    stock_payload = StockService.fetch_stock_analysis()
    print(f"✅ fetch_stock_analysis output length: {len(stock_payload.get('text', ''))}")
except Exception as e:
    print(f"❌ fetch_stock_analysis FAILED: {e}")


# 2. MARKET SERVICE
print("\n--- MARKET SERVICE ---")
validate_api("Market Breadth (HOSE)", MarketService._fetch_cafef_market_breadth)
validate_api("Prop Trading (Tu Doanh)", MarketService._fetch_cafef_prop_trading)
validate_api("Exchange Rates", MarketService._fetch_cafef_exchange_rates)
validate_api("Foreign Flow", MarketService._fetch_cafef_foreign_flow)
validate_api("Commodities", MarketService._fetch_cafef_commodities)
validate_api("Global Indices", MarketService._fetch_cafef_global)
validate_api("Market Leaders", MarketService._fetch_cafef_leaders)

# 3. BANKING SERVICE
print("\n--- BANKING SERVICE ---")
validate_api("Interest Rates", BankingService._fetch_raw_interest_rates)
# Banking Rates wrapper
val_bank = BankingService.fetch_banking_rates()
if val_bank and "text" in val_bank and len(val_bank["text"]) > 20:
    print(f"✅ fetch_banking_rates: OK (Text len={len(val_bank['text'])})")
else:
    print(f"❌ fetch_banking_rates: FAILED")

print("\n---------------------------------------")
