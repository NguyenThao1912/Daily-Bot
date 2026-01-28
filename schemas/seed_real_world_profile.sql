-- Seed "Real World Profile" (No RPG Terms)
-- NOTE: Replace 'YOUR_TELEGRAM_ID_HERE' with your actual Telegram User ID (numeric string)

INSERT INTO profiles (telegram_id, full_name, job_title, seniority_level, physical_health, mental_status, available_time, cash_on_hand, safety_fund, assets_portfolio, infrastructure, traits, personal_goals)
VALUES (
    'YOUR_TELEGRAM_ID_HERE', 
    'The Pragmatic Builder', 
    'Software Engineer',     
    '10 Years Experience',   
    'Sedentary / Neck Pain', 
    'High Focus / Stress',   
    'Evenings (20h-22h)',    
    50000000, -- VND
    200000000, -- VND
    '{
        "investments": {
            "High Risk": "VN-Index",
            "Safe": "Gold SJC, USD",
            "Debt": "Credit Card (Due 25th)"
        }
    }',
    '{
        "primary_income": "Tech Lead Salary",
        "secondary_income": "Freelance",         
        "transport": "GrabBiz / Public Transport" 
    }',
    '{
        "style": "Pragmatic",        
        "strengths": ["Automation Mindset", "Risk Aversion"], 
        "weaknesses": ["Information Overload", "FOMO"]       
    }',
    '{
        "long_term": {
            "objective": "Build Personal AI System ($0 Cost)" 
        },
        "short_term": [
            "Optimize Workflow",  
            "Smart Shopping (Tech Deals)"
        ],
        "routines": [
            "Daily Scrum (09:30)", 
            "Check Metrics (17:00)"
        ]
    }'
)
ON CONFLICT (telegram_id) 
DO UPDATE SET
    job_title = EXCLUDED.job_title,
    seniority_level = EXCLUDED.seniority_level,
    physical_health = EXCLUDED.physical_health,
    mental_status = EXCLUDED.mental_status,
    available_time = EXCLUDED.available_time,
    cash_on_hand = EXCLUDED.cash_on_hand,
    safety_fund = EXCLUDED.safety_fund,
    assets_portfolio = EXCLUDED.assets_portfolio,
    infrastructure = EXCLUDED.infrastructure,
    traits = EXCLUDED.traits,
    personal_goals = EXCLUDED.personal_goals;
