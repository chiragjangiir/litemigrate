# SQLite Architectural Glossary

- **WAL (Write-Ahead Log)**: Concurrency mode appending transactions sequentially to a separate `-wal` file.
- **Checkpoint**: Flushing committed WAL frames back into the main database b-tree pages.
- **Shadow Verification**: Validating migrations in an ephemeral filesystem clone before production promotion.
