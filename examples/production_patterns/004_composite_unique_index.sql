-- Migration: Create composite unique index covering tenant and user email
CREATE UNIQUE INDEX IF NOT EXISTS idx_tenant_user_email ON users(tenant_id, email);
