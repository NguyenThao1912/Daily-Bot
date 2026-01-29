from src.config import Config

class WatchlistService:
    @staticmethod
    def get_watchlist(chat_id: str, category: str = "stock"):
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            return []
        
        try:
            from supabase import create_client
            supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            
            # Use str for chat_id as stored in DB for consistency with worker
            res = supabase.table("watchlists") \
                .select("items") \
                .eq("chat_id", str(chat_id)) \
                .eq("category", category) \
                .single() \
                .execute()
            
            if res.data:
                return res.data.get("items", [])
            return []
        except Exception as e:
            print(f"⚠️ Watchlist DB Error: {e}")
            return []
