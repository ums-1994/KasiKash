-- Migrate gamification tables to use Firebase UID as user_id

-- user_badges
ALTER TABLE user_badges ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
UPDATE user_badges ub SET temp_user_id = u.firebase_uid FROM users u WHERE ub.user_id = u.id;
ALTER TABLE user_badges DROP CONSTRAINT IF EXISTS user_badges_user_id_fkey;
ALTER TABLE user_badges DROP COLUMN user_id;
ALTER TABLE user_badges ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE user_badges RENAME COLUMN temp_user_id TO user_id;
ALTER TABLE user_badges ADD CONSTRAINT user_badges_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

-- user_points
ALTER TABLE user_points ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
UPDATE user_points up SET temp_user_id = u.firebase_uid FROM users u WHERE up.user_id = u.id;
ALTER TABLE user_points DROP CONSTRAINT IF EXISTS user_points_user_id_fkey;
ALTER TABLE user_points DROP COLUMN user_id;
ALTER TABLE user_points ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE user_points RENAME COLUMN temp_user_id TO user_id;
ALTER TABLE user_points ADD CONSTRAINT user_points_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

-- streaks
ALTER TABLE streaks ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
UPDATE streaks s SET temp_user_id = u.firebase_uid FROM users u WHERE s.user_id = u.id;
ALTER TABLE streaks DROP CONSTRAINT IF EXISTS streaks_user_id_fkey;
ALTER TABLE streaks DROP COLUMN user_id;
ALTER TABLE streaks ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE streaks RENAME COLUMN temp_user_id TO user_id;
ALTER TABLE streaks ADD CONSTRAINT streaks_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

-- user_levels
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
UPDATE user_levels ul SET temp_user_id = u.firebase_uid FROM users u WHERE ul.user_id = u.id;
ALTER TABLE user_levels DROP CONSTRAINT IF EXISTS user_levels_user_id_fkey;
ALTER TABLE user_levels DROP COLUMN user_id;
ALTER TABLE user_levels ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE user_levels RENAME COLUMN temp_user_id TO user_id;
ALTER TABLE user_levels ADD CONSTRAINT user_levels_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

-- user_achievements
ALTER TABLE user_achievements ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
UPDATE user_achievements ua SET temp_user_id = u.firebase_uid FROM users u WHERE ua.user_id = u.id;
ALTER TABLE user_achievements DROP CONSTRAINT IF EXISTS user_achievements_user_id_fkey;
ALTER TABLE user_achievements DROP COLUMN user_id;
ALTER TABLE user_achievements ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE user_achievements RENAME COLUMN temp_user_id TO user_id;
ALTER TABLE user_achievements ADD CONSTRAINT user_achievements_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE;

-- user_challenges
ALTER TABLE user_challenges ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(128);
UPDATE user_challenges uc SET temp_user_id = u.firebase_uid FROM users u WHERE uc.user_id = u.id;
ALTER TABLE user_challenges DROP CONSTRAINT IF EXISTS user_challenges_user_id_fkey;
ALTER TABLE user_challenges DROP COLUMN user_id;
ALTER TABLE user_challenges ALTER COLUMN temp_user_id SET NOT NULL;
ALTER TABLE user_challenges RENAME COLUMN temp_user_id TO user_id;
ALTER TABLE user_challenges ADD CONSTRAINT user_challenges_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(firebase_uid) ON DELETE CASCADE; 