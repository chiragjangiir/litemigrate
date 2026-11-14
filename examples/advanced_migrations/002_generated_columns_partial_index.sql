-- Migration: Add generated columns and conditional partial index
BEGIN TRANSACTION;

-- Add virtual generated column computing normalized search terms
ALTER TABLE products ADD COLUMN sku_prefix TEXT GENERATED ALWAYS AS (substr(sku, 1, 4)) STORED;

-- Add partial index covering active in-stock merchandise only
CREATE INDEX idx_products_active_stock ON products(id, stock_count)
WHERE status = 'active' AND stock_count > 0;

COMMIT;
