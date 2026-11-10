-- Safe migration: Add bio column and index
ALTER TABLE users ADD COLUMN bio TEXT;
CREATE INDEX idx_users_bio ON users(bio);
