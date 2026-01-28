-- Seed "Citizen Profile"
-- NOTE: Replace 'YOUR_TELEGRAM_ID_HERE' with your actual Telegram User ID (numeric string)

INSERT INTO profiles (telegram_id, full_name, role, seniority, physical_health, mental_state, available_time, gold_amount, stash_amount, inventory, equipment, traits, quest_log)
VALUES (
    'YOUR_TELEGRAM_ID_HERE', 
    'The Pragmatic Builder', -- Tên hiển thị
    'Software Engineer',     -- rpg_class -> Vai trò
    '10 Years Experience',   -- rpg_level -> Thâm niên
    'Sedentary / Neck Pain', -- hp_status -> Thể chất
    'High Focus / Stress',   -- mp_status -> Tinh thần
    'Evenings (20h-22h)',    -- time_mana -> Quỹ thời gian
    50000000, -- Tiền mặt
    200000000, -- Quỹ dự phòng
    '{
        "investments": {
            "High Risk": "VN-Index",
            "Safe": "Gold SJC, USD",
            "Debt": "Credit Card (Due 25th)"
        }
    }',
    '{
        "main_hand": "Tech Lead Salary", -- Nguồn thu chính
        "off_hand": "Freelance",         -- Nguồn thu phụ
        "mount": "GrabBiz / Public Transport" -- Phương tiện
    }',
    '{
        "alignment": "Pragmatic",        -- Phong cách
        "buffs": ["Automation Mindset", "Risk Aversion"], -- Điểm mạnh
        "debuffs": ["Information Overload", "FOMO"]       -- Điểm yếu
    }',
    '{
        "main_quest": {
            "objective": "Build Personal AI System ($0 Cost)" -- Mục tiêu dài hạn
        },
        "side_quests": [
            "Optimize Workflow",  -- Ưu tiên ngắn hạn
            "Smart Shopping (Tech Deals)"
        ],
        "daily_grind": [
            "Daily Scrum (09:30)", -- Lịch trình
            "Check Metrics (17:00)"
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
