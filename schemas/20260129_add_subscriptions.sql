-- Create subscriptions table
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL, -- e.g. "Netflix", "AWS", "Tiền nhà"
    cost NUMERIC NOT NULL, -- e.g. 260000
    currency TEXT DEFAULT 'VND', -- 'VND' or 'USD'
    billing_cycle TEXT CHECK (billing_cycle IN ('monthly', 'yearly', 'weekly')) DEFAULT 'monthly',
    next_due_date DATE NOT NULL,
    status TEXT CHECK (status IN ('active', 'cancelled')) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for querying upcoming bills
CREATE INDEX idx_subscriptions_next_due_date ON subscriptions (next_due_date);

-- Seed Example Data
-- INSERT INTO subscriptions (profile_id, name, cost, next_due_date)
-- VALUES 
-- ((SELECT id FROM profiles WHERE telegram_id = 'YOUR_ID'), 'Netflix Premium', 260000, '2026-02-05'),
-- ((SELECT id FROM profiles WHERE telegram_id = 'YOUR_ID'), 'Tiền Nhà', 8000000, '2026-02-01');
