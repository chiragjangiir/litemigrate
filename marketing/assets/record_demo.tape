Output marketing/assets/litemigrate_demo.mp4
Output marketing/assets/litemigrate_demo.gif

Set FontSize 14
Set Width 1100
Set Height 680
Set Theme "Catppuccin Mocha"
Set Padding 18
Set Framerate 30

# Initialize environment
Hide
Type "source /tmp/litemigrate_demo_env/bin/activate && cd /tmp/litemigrate_recording" Enter
Type "clear" Enter
Show

# Title Card
Type "# LiteMigrate (v0.1.0-alpha.1) — Shadow SQLite Migration Safety Demo" Sleep 500ms Enter
Type "# Scene 1: Inspect disposable database contents" Sleep 500ms Enter
Sleep 1s
Type "sqlite3 app.db '.tables'" Sleep 500ms Enter
Sleep 1.5s
Type "sqlite3 app.db 'SELECT * FROM parent_users;'" Sleep 500ms Enter
Sleep 2s

# Scene 2: Show migration script
Type "# Scene 2: View additive migration SQL" Sleep 500ms Enter
Type "cat safe_migration.sql" Sleep 500ms Enter
Sleep 2s

# Scene 3: Inspect database
Type "# Scene 3: Inspect database schema & invariants" Sleep 500ms Enter
Type "litemigrate inspect --db app.db" Sleep 500ms Enter
Sleep 3s

# Scene 4: Validate on shadow copy
Type "# Scene 4: Validate on isolated shadow sandbox (app.db untouched)" Sleep 500ms Enter
Type "litemigrate validate --db app.db --migration safe_migration.sql --output audit.json" Sleep 500ms Enter
Sleep 3.5s

# Scene 5: Display audit report
Type "# Scene 5: Inspect generated audit report" Sleep 500ms Enter
Type "litemigrate report --input audit.json" Sleep 500ms Enter
Sleep 3s

# Scene 6: Demonstrate blocked unsafe migration
Type "# Scene 6: Demonstrate unsafe cascade deletion being blocked" Sleep 500ms Enter
Type "cat unsafe_migration.sql" Sleep 500ms Enter
Sleep 1.5s
Type "litemigrate validate --db app.db --migration unsafe_migration.sql" Sleep 500ms Enter
Sleep 4s

# Scene 7: Safe Promotion
Type "# Scene 7: Safely promote validated migration to source" Sleep 500ms Enter
Type "litemigrate apply --db app.db --migration safe_migration.sql --confirm" Sleep 500ms Enter
Sleep 3.5s
Type "sqlite3 app.db '.schema parent_users'" Sleep 500ms Enter
Sleep 3s

