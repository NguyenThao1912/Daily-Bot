AGENT_LABELS = {
    "weather": "WEATHER & TRAFFIC",
    "calendar": "LUNAR CALENDAR & FORTUNE",
    "finance": "FINANCE",
    "news": "DAILY NEWS",
    "trends": "GOOGLE TRENDS & VIRAL",
    "tech": "TECHNOLOGY & AI",
}

VN30_TICKERS = [
    "ACB", "SHB", "DGC", "BID", "CTG", "FPT", "GAS", "HPG", "MBB", "MSN",
    "MWG", "SSI", "STB", "VCB", "VIC", "VNM", "SAB", "VIB", "VJC", "PLX",
    "VPB", "LPB", "VRE", "HDB", "BCM", "VHM", "GVR", "TPB", "TCB", "SSB",
]

GOOGLE_NEWS_QUERIES = {
    "general": [
        "Vietnam policy OR regulation OR government OR public safety OR public health when:1d",
        "Vietnam economy OR inflation OR trade OR energy OR infrastructure when:1d",
        "Vietnam health OR disease outbreak OR hospital OR epidemic OR CDC when:1d",
        "Vietnam storm OR flood OR landslide OR earthquake OR disaster when:1d",
        "world economy OR geopolitics OR supply chain OR oil prices OR war OR conflict when:1d",
    ],
    "featured": [
        "Vietnam breaking news OR urgent OR investigation OR disruption OR emergency when:1d",
        "Vietnam headlines OR policy shift OR major incident OR outbreak OR disaster when:1d",
        "war OR military conflict OR missile OR evacuation OR humanitarian crisis when:1d",
        "Asia markets OR global markets OR macro risk OR epidemic risk when:1d",
    ],
    "business": [
        "Vietnam business OR economy OR industry OR exports OR FDI when:1d",
        "Vietnam banking OR interest rates OR real estate OR manufacturing when:1d",
        "Vietnam market OR earnings OR M&A OR investment when:1d",
    ],
    "tech": [
        "AI model OR AI tool OR generative AI OR LLM when:1d",
        "cybersecurity OR cloud OR semiconductor OR developer tools when:1d",
        "startup funding OR product launch OR platform update OR software when:1d",
    ],
}

GOOGLE_NEWS_PRIORITY_KEYWORDS = {
    "general": [
        "kinh te", "lạm phát", "inflation", "trade", "xuat khau", "export",
        "dau", "oil", "quy dinh", "regulation", "chinh sach", "policy",
        "an ninh", "security", "ha tang", "infrastructure", "dien", "energy",
        "y te", "health", "dich benh", "outbreak", "epidemic", "virus",
        "benh vien", "hospital", "cdc", "flood", "lu", "bao", "storm",
        "landslide", "dong dat", "earthquake", "disaster", "war", "chien tranh",
        "conflict", "missile", "evacuation", "humanitarian",
    ],
    "featured": [
        "breaking", "urgent", "risk", "canh bao", "warning", "investigation",
        "policy", "regulation", "incident", "disruption", "markets",
        "outbreak", "health", "disaster", "storm", "flood", "war",
        "conflict", "military", "evacuation", "humanitarian",
    ],
    "business": [
        "ngan hang", "bank", "lai suat", "interest", "real estate", "bat dong san",
        "earnings", "M&A", "fdi", "manufacturing", "investment", "export",
    ],
    "tech": [
        "ai", "model", "llm", "chip", "semiconductor", "cloud", "security",
        "cyber", "developer", "platform", "openai", "google", "microsoft",
    ],
}

GOOGLE_NEWS_EXCLUDED_KEYWORDS = [
    "showbiz", "giai tri", "entertainment", "celebrity", "hoa hau",
    "bong da", "football", "soccer", "the thao", "sports", "esports",
    "phim", "movie", "drama", "music", "idol", "concert", "tu vi",
]

VN30_IMPACT_KEYWORDS = [
    "interest rate", "lai suat", "inflation", "lạm phát", "ty gia", "exchange rate",
    "usd", "oil", "dau", "energy", "electricity", "power", "trade", "tariff",
    "export", "supply chain", "logistics", "credit", "banking", "ngan hang",
    "real estate", "bat dong san", "steel", "thep", "consumer", "retail",
    "technology", "ai", "semiconductor", "cybersecurity", "fdi", "manufacturing",
    "regulation", "policy", "public investment", "ha tang", "infrastructure",
    "health", "disease", "outbreak", "storm", "flood", "disaster",
    "war", "conflict", "geopolitics", "sanctions",
]

VN30_COMPANY_ALIASES = {
    "ACB": ["acb", "asia commercial bank"],
    "BCM": ["bcm", "becamex"],
    "BID": ["bid", "bidv"],
    "CTG": ["ctg", "vietinbank"],
    "DGC": ["dgc", "duc giang"],
    "FPT": ["fpt"],
    "GAS": ["gas", "pv gas"],
    "GVR": ["gvr", "cao su", "vinachem", "vrg"],
    "HDB": ["hdb", "hdbank"],
    "HPG": ["hpg", "hoa phat"],
    "LPB": ["lpb", "lpbank", "lien viet"],
    "MBB": ["mbb", "mb bank", "mbbank"],
    "MSN": ["msn", "masan"],
    "MWG": ["mwg", "the gioi di dong"],
    "PLX": ["plx", "petrolimex"],
    "SAB": ["sab", "sabeco"],
    "SHB": ["shb"],
    "SSB": ["ssb", "seabank"],
    "SSI": ["ssi", "ssi securities"],
    "STB": ["stb", "sacombank"],
    "TCB": ["tcb", "techcombank"],
    "TPB": ["tpb", "tpbank"],
    "VCB": ["vcb", "vietcombank"],
    "VHM": ["vhm", "vinhomes"],
    "VIB": ["vib"],
    "VIC": ["vic", "vingroup", "vinfast"],
    "VJC": ["vjc", "vietjet"],
    "VNM": ["vnm", "vinamilk"],
    "VPB": ["vpb", "vpbank"],
    "VRE": ["vre", "vincom retail"],
}
