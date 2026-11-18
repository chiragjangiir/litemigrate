# SQLite Indexing Best Practices & Query Optimization

## 1. Partial Indexes
Reduce index storage and write overhead by indexing only relevant subsets:
```sql
CREATE INDEX idx_pending_orders ON orders(created_at) WHERE status = 'pending';
```

## 2. Covering Indexes
Include lookup columns directly in the index to satisfy queries from index B-trees without table lookups:
```sql
CREATE INDEX idx_users_login ON users(email, password_hash, id);
```

## 3. Expression Indexes
Index deterministic function outputs:
```sql
CREATE INDEX idx_users_lower_email ON users(lower(email));
```
