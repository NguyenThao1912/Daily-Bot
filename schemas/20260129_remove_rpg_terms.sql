-- Migration: Rename RPG Columns to Real World Terms
ALTER TABLE profiles RENAME COLUMN rpg_class TO role;
ALTER TABLE profiles RENAME COLUMN rpg_level TO seniority;
ALTER TABLE profiles RENAME COLUMN hp_status TO physical_health;
ALTER TABLE profiles RENAME COLUMN mp_status TO mental_state;
ALTER TABLE profiles RENAME COLUMN time_mana TO available_time;
ALTER TABLE profiles RENAME COLUMN gold_amount TO cash_on_hand;
ALTER TABLE profiles RENAME COLUMN stash_amount TO safety_fund;
ALTER TABLE profiles RENAME COLUMN quest_log TO personal_goals;

-- Update column comments/types if needed
COMMENT ON COLUMN profiles.role IS 'Job Title or Role (e.g. Software Engineer)';
COMMENT ON COLUMN profiles.seniority IS 'Years of Experience or Level';
COMMENT ON COLUMN profiles.cash_on_hand IS 'Liquid Cash (VND)';
COMMENT ON COLUMN profiles.safety_fund IS 'Emergency Fund (VND)';

-- Add new columns if missing from seed
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'Citizen';
