# Mysql Insert only if not exists

Nice — there are several ways to “insert only if not exists” in MySQL depending on your constraints and concurrency needs. Below I show the common patterns, explain when to use each, and include safe/recommended approaches.

# 1) Best practice — enforce uniqueness + use `INSERT ... ON DUPLICATE KEY UPDATE` (recommended)

Create a UNIQUE index on the column(s) that define “exists”. This prevents race conditions and is efficient.

```sql
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(100),
  UNIQUE KEY ux_email (email)
);
```

Then insert and do a no-op update on duplicate key:

```sql
INSERT INTO users (email, name)
VALUES ('alice@example.com', 'Alice')
ON DUPLICATE KEY UPDATE id = id; -- no-op update
```

If you want the `id` whether inserted or already present, use the `LAST_INSERT_ID()` trick:

```sql
INSERT INTO users (email, name)
VALUES ('alice@example.com', 'Alice')
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

-- then get the id
SELECT LAST_INSERT_ID(); -- returns the row id (new or existing)
```

# 2) `INSERT IGNORE` (simple, but silent failures)

If duplicate-key errors should be ignored and you don't need to know if insert happened:

```sql
INSERT IGNORE INTO users (email, name)
VALUES ('alice@example.com', 'Alice');
```

Notes: it silently ignores duplicate-key errors and other warnings; not good if you need to detect the outcome.

# 3) `REPLACE INTO` (not usually recommended)

`REPLACE` deletes the existing row and inserts the new one — it can have side effects (triggers, cascades, new auto-increment id):

```sql
REPLACE INTO users (email, name) VALUES ('alice@example.com', 'Alice');
```

Use only when replacing the whole row is acceptable.

# 4) `INSERT ... SELECT ... WHERE NOT EXISTS` (works without unique index, but race-prone)

If you cannot add a unique index and accept possible race conditions:

```sql
INSERT INTO users (email, name)
SELECT 'alice@example.com', 'Alice'
FROM DUAL
WHERE NOT EXISTS (
  SELECT 1 FROM users WHERE email = 'alice@example.com'
);
```

This can still suffer from race conditions under concurrency — two transactions might see “not exists” simultaneously and both insert. To avoid that, prefer a unique constraint.

# 5) Transaction + explicit locks (advanced)

You can serialize access by locking the table/rows, but it's less scalable. Example sketch:

```sql
START TRANSACTION;
LOCK TABLES users WRITE;

-- check + insert
INSERT INTO users (email, name)
SELECT 'alice@example.com', 'Alice'
FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email='alice@example.com');

UNLOCK TABLES;
COMMIT;
```

This prevents races but reduces concurrency — prefer unique index approach.

# Quick decision guide

* You **care about correctness under concurrency** → add a UNIQUE index and use `INSERT ... ON DUPLICATE KEY UPDATE` (or `INSERT IGNORE`) — recommended.
* You want a **simple one-off** and don't need to know outcome → `INSERT IGNORE`.
* You want to **replace** existing rows → `REPLACE INTO`.
* You can't add a unique index and low concurrency → `INSERT ... SELECT ... WHERE NOT EXISTS` (but be aware of race conditions).

If you tell me the table schema and which columns define “exists” (or paste an example row), I can give the exact SQL you should use (including a `LAST_INSERT_ID()` variant if you need the row id).
