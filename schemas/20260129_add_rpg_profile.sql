-- Add RPG Profile columns to existing profiles table
ALTER TABLE profiles
ADD COLUMN rpg_class TEXT, -- e.g. "Tech Lead", "Founder"
ADD COLUMN rpg_level TEXT, -- e.g. "Senior", "Master"
ADD COLUMN hp_status TEXT, -- Health status description
ADD COLUMN mp_status TEXT, -- Mental status description
ADD COLUMN time_mana TEXT, -- Time availability description
ADD COLUMN gold_amount NUMERIC DEFAULT 0, -- Cash on hand
ADD COLUMN stash_amount NUMERIC DEFAULT 0, -- Emergency fund
ADD COLUMN inventory JSONB DEFAULT '{}', -- Assets, Investments, Debts
ADD COLUMN equipment JSONB DEFAULT '{}', -- Main Job, Side Hustle, Vehicle
ADD COLUMN traits JSONB DEFAULT '{}', -- Alignment, Buffs, Debuffs
ADD COLUMN quest_log JSONB DEFAULT '{}'; -- Main, Side, Daily quests

-- Helper function to update RPG stats easily
CREATE OR REPLACE FUNCTION update_rpg_stats(
  p_telegram_id TEXT,
  p_hp TEXT,
  p_mp TEXT,
  p_gold NUMERIC
) RETURNS VOID AS $$
BEGIN
  UPDATE profiles
  SET hp_status = p_hp, mp_status = p_mp, gold_amount = p_gold
  WHERE telegram_id = p_telegram_id;
END;
$$ LANGUAGE plpgsql;
