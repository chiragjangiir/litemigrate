# Basic Migration Example

Demonstrates a standard, non-destructive migration that adds a new column and creates an index.

## Step 1: Create the baseline database

```bash
sqlite3 app.db < schema.sql
```

## Step 2: Inspect the database

```bash
litemigrate inspect --db ./app.db
```

## Step 3: Validate the migration against an isolated shadow copy

```bash
litemigrate validate --db ./app.db --migration ./001_add_user_bio.sql
```

Notice that `app.db` remains untouched.

## Step 4: Apply the migration safely

```bash
litemigrate apply --db ./app.db --migration ./001_add_user_bio.sql --confirm
```

A pre-promotion backup is created automatically, and the migration is replayed inside an atomic writer transaction.
