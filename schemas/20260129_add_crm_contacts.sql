-- Create contacts table for Personal CRM
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL, -- e.g. "Vợ", "Mẹ", "Sếp"
    relationship TEXT, -- e.g. "Spouse", "Parent", "Partner"
    
    -- Personal Info
    birthday DATE, -- YYYY-MM-DD
    age INTEGER, -- Can be derived from birthday, but user asked for it explicitly or as cache
    marital_status TEXT, -- 'Single', 'Married', 'Divorced'
    job_title TEXT, -- 'Marketing Manager', 'CEO'
    phone_number TEXT,
    address TEXT,
    
    -- Insights
    strengths TEXT[], -- e.g. ["Giao tiếp", "Kỹ tính", "Thích được khen"]
    preferences JSONB DEFAULT '{}', -- { "wishlist": ["Son MAC", "Hoa"], "dislikes": ["Hải sản"] }
    
    -- Events
    anniversary DATE, -- Optional
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster date querying
CREATE INDEX idx_contacts_birthday ON contacts (birthday);
CREATE INDEX idx_contacts_anniversary ON contacts (anniversary);

-- Buffer Seed data (Example)
-- INSERT INTO contacts (profile_id, name, relationship, birthday, job_title, strengths, phone_number)
-- VALUES (
--   (SELECT id FROM profiles WHERE telegram_id = 'YOUR_ID'),
--   'Vợ Yêu',
--   'Spouse',
--   '1995-02-02',
--   'Banker',
--   ARRAY['Chu đáo', 'Nấu ăn ngon'],
--   '0988xxxxxx'
-- );
