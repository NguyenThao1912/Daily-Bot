-- Seed "The Pragmatic Builder" Profile
-- NOTE: Replace 'YOUR_TELEGRAM_ID_HERE' with your actual Telegram User ID (numeric string)

INSERT INTO profiles (telegram_id, full_name, role, seniority, physical_health, mental_state, available_time, gold_amount, stash_amount, inventory, equipment, traits, quest_log)
VALUES (
    'YOUR_TELEGRAM_ID_HERE', 
    'The Pragmatic Builder',
    'Techno-Investor', -- rpg_class mapped to role
    'Mid-Senior', -- rpg_level mapped to seniority
    'Healthy (Sedentary)', -- hp_status
    'High Efficiency / Notification Fatigue', -- mp_status
    'Limited (High Opportunity Cost)', -- time_mana
    50000000, -- Liquid Cash (Estimated)
    200000000, -- Emergency Fund (Estimated)
    '{
        "investments": {
            "Crypto": "Bitcoin (High Risk)",
            "Stocks": "VN-Index (Macro Aware)",
            "Safe Haven": "Gold SJC (Real-time)",
            "Currencies": "USD/VND"
        }
    }',
    '{
        "main_hand": "Python / Automation",
        "off_hand": "Telegram Bot Builder",
        "mount": "GrabBiz / Public Transport"
    }',
    '{
        "alignment": "Lawful Efficient",
        "buffs": ["Zero Cost Architect", "Risk Aversion"],
        "debuffs": ["Time Poor", "Notification Fatigue"]
    }',
    '{
        "main_quest": {
            "objective": "Build The Morning Oracle (Cost $0, High Impact)"
        },
        "side_quests": [
            "Monitor Infra Costs (Free Tier)",
            "Optimize Workflow (Set and Forget)",
            "Smart Shopping (Uniqlo/Shopee Tech)"
        ],
        "daily_grind": [
            "Check Macro Indicators (DXY, Yields)",
            "Review Bot Performance"
        ]
    }'
)
ON CONFLICT (telegram_id) 
DO UPDATE SET
    role = EXCLUDED.role,
    seniority = EXCLUDED.seniority,
    physical_health = EXCLUDED.physical_health,
    mental_state = EXCLUDED.mental_state,
    available_time = EXCLUDED.available_time,
    gold_amount = EXCLUDED.gold_amount,
    stash_amount = EXCLUDED.stash_amount,
    inventory = EXCLUDED.inventory,
    equipment = EXCLUDED.equipment,
    traits = EXCLUDED.traits,
    quest_log = EXCLUDED.quest_log;
