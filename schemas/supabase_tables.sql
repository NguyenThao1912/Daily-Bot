-- Profiles table to store user settings
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id TEXT UNIQUE NOT NULL,
    full_name TEXT,
    home_location TEXT, -- e.g. "Quận 7, HCM"
    work_location TEXT, -- e.g. "Quận 1, HCM"
    commute_time TIME DEFAULT '07:45:00',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Categories of news/briefs
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL, -- e.g. "finance", "weather", "shopping"
    prompt_template TEXT NOT NULL,
    priority INTEGER DEFAULT 1
);

-- User interests/tracking within each category
CREATE TABLE user_interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    keywords JSONB DEFAULT '[]', -- e.g. ["FPT", "HPG", "BTC"]
    metadata JSONB DEFAULT '{}' -- e.g. budgets, specific items
);

-- History of generated reports
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'sent',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reminders for time-sensitive events (e.g. 1 hour before a sale)
CREATE TABLE reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, sent, expired
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Seed initial categories
INSERT INTO categories (name, prompt_template) VALUES 
('finance', 'Bạn là chuyên gia tài chính. Phân tích mã {keywords} và giá vàng/BTC. Đưa ra Action: Mua/Bán/Gia tăng.'),
('weather', 'Bạn là chuyên gia khí tượng. Phân tích thời tiết tại {location}. Cảnh báo kẹt xe từ {home} đến {work}.'),
('shopping', 'Bạn là chuyên gia săn deal trên Shopee, Uniqlo, ShopeeFood. Tìm ưu đãi cho {keywords}. Nếu có deal sốc có giờ bắt đầu cụ thể, hãy đánh dấu là [URGENT] kèm giờ.');
