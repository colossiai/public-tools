# MySQL Tutorial: Using `INNER JOIN` as a Filter

A beginner-friendly walkthrough of a pattern that confuses a lot of people:
**an `INNER JOIN` can be used not to add columns, but to keep or drop rows** —
i.e. as a filter. We'll build it up from zero with tables you can paste into any
MySQL and run.

---

## 1. What an `INNER JOIN` normally does

A join *combines* rows from two tables where a condition matches. Start with two
tiny tables: articles, and the tags attached to each article.

```sql
CREATE TABLE news (
  id    INT PRIMARY KEY,
  title VARCHAR(100)
);

CREATE TABLE news_tag (
  news_id  INT,
  tag_type VARCHAR(16),   -- 'ticker' or 'label'
  tag      VARCHAR(32),
  -- one tag can appear at most once per article:
  UNIQUE KEY uniq_tag (news_id, tag_type, tag)
);

INSERT INTO news VALUES
  (1, 'Apple earnings beat'),
  (2, 'Apple hires new CFO'),
  (3, 'Google earnings beat'),
  (4, 'Market wrap');

INSERT INTO news_tag VALUES
  (1, 'ticker', 'AAPL.US'),
  (1, 'label',  'earnings'),
  (2, 'ticker', 'AAPL.US'),
  (3, 'ticker', 'GOOG.US'),
  (3, 'label',  'earnings');
-- (article 4 has no tags)
```

A normal join — "show me each article together with its tags":

```sql
SELECT news.id, news.title, news_tag.tag_type, news_tag.tag
FROM news
INNER JOIN news_tag ON news_tag.news_id = news.id;
```

Result:

```
id | title                | tag_type | tag
 1 | Apple earnings beat  | ticker   | AAPL.US
 1 | Apple earnings beat  | label    | earnings
 2 | Apple hires new CFO  | ticker   | AAPL.US
 3 | Google earnings beat | ticker   | GOOG.US
 3 | Google earnings beat | label    | earnings
```

Two things to notice already:

- **Article 4 disappeared.** It has no matching tag row, and `INNER JOIN` keeps
  only rows that have a match. (That is the seed of the whole idea — keep reading.)
- **Article 1 appears twice.** It has two tags, so the join produced two rows.
  This is called **fan-out** (one left row → many output rows).

---

## 2. The idea: a join that *filters* instead of *expanding*

Suppose you don't care about the tag columns at all. You just want:

> "Give me the articles that are tagged `ticker = AAPL.US`."

You can push the tag value *into the join condition* and select only the article
columns:

```sql
SELECT news.id, news.title
FROM news
INNER JOIN news_tag ON news_tag.news_id = news.id
                   AND news_tag.tag_type = 'ticker'
                   AND news_tag.tag      = 'AAPL.US';
```

Result:

```
id | title
 1 | Apple earnings beat
 2 | Apple hires new CFO
```

Articles 3 and 4 are gone — 3 is Google, 4 has no tags. The join kept **only**
the articles that have an `AAPL.US` ticker edge. We used the join purely to
**filter rows**, and selected nothing from the joined table. That's "`INNER JOIN`
as a filter."

> Putting the tag conditions in `ON` vs `WHERE` makes **no difference for an
> INNER JOIN** — `ON news_tag.tag='AAPL.US'` and `WHERE news_tag.tag='AAPL.US'`
> give the same result. Keeping them in `ON` just reads nicely ("this is part of
> how I join").

---

## 3. The catch: filtering only works cleanly when the match is unique

Remember article 1 appeared **twice** in section 1 because it had two tags. What
if an article could carry the *same* tag more than once? Let's simulate a
duplicate (temporarily dropping the unique key):

```sql
-- imagine uniq_tag did NOT exist and this second copy got inserted:
INSERT INTO news_tag VALUES (2, 'ticker', 'AAPL.US');  -- duplicate for article 2
```

Now re-run the filter query from section 2. Article 2 would come back **twice**:

```
id | title
 1 | Apple earnings beat
 2 | Apple hires new CFO
 2 | Apple hires new CFO    <-- duplicate!
```

This is the key lesson:

> **An `INNER JOIN` is only a clean filter when the right-hand side matches at
> most one row.** If it can match several, the join *multiplies* rows (fan-out)
> and you get duplicates.

In our schema the `UNIQUE KEY uniq_tag (news_id, tag_type, tag)` guarantees at
most one row per `(news_id, tag_type, tag)`. So each specific tag condition
matches **≤ 1** row, no duplicates, and the join behaves as a pure filter — this
is why real queries on this table need **no `DISTINCT`**.

If you *don't* have that guarantee, you have two fixes (see section 6).

---

## 4. Two joins = AND (intersection)

Now the powerful part. What if you want:

> "Articles that are tagged `ticker = AAPL.US` **AND** `label = earnings`."

One join can only test one `(tag_type, tag)`, because a single `news_tag` row is
*either* a ticker row *or* a label row — never both at once. So you join the tag
table **twice**, each with its own alias, each pinned to one condition:

```sql
SELECT news.id, news.title
FROM news
INNER JOIN news_tag t0 ON t0.news_id = news.id
                      AND t0.tag_type = 'ticker' AND t0.tag = 'AAPL.US'
INNER JOIN news_tag t1 ON t1.news_id = news.id
                      AND t1.tag_type = 'label'  AND t1.tag = 'earnings';
```

Result (after removing the duplicate from section 3):

```
id | title
 1 | Apple earnings beat
```

Only article 1 survives:

- Article 1 has both edges → matches `t0` **and** `t1` → kept.
- Article 2 has the ticker but no `earnings` label → `t1` finds nothing → dropped.
- Article 3 has `earnings` but ticker is `GOOG.US`, not `AAPL.US` → `t0` finds
  nothing → dropped.

Each extra `INNER JOIN` adds one more **"must also have this"** condition. That's
how you express **set intersection** across rows that live in separate tag rows.

> Careful: this is an **AND** (intersection). A common beginner mistake is
> `WHERE tag IN ('AAPL.US','earnings')` — that's an **OR** (union): it matches an
> article that has *either* tag, which is not what we want.

---

## 5. The same filter written as `EXISTS`

The "join-as-filter" pattern has a twin that says the intent more explicitly:
`EXISTS`. These two queries return the same rows as section 4:

```sql
SELECT news.id, news.title
FROM news
WHERE EXISTS (SELECT 1 FROM news_tag
              WHERE news_id = news.id AND tag_type='ticker' AND tag='AAPL.US')
  AND EXISTS (SELECT 1 FROM news_tag
              WHERE news_id = news.id AND tag_type='label'  AND tag='earnings');
```

Differences to understand:

| | `INNER JOIN` (unique key) | `EXISTS` |
|---|---|---|
| Duplicates? | None *because* the key is unique | **Never**, even without a unique key (`EXISTS` just asks "any match?") |
| Reads like | "combine, then keep matches" | "keep rows for which a match exists" |
| Can select joined columns? | Yes (`t0.*`, `t1.*`) | No (subquery is only a test) |

Rule of thumb: if you actually **need columns** from the matched rows, use a
JOIN. If you only need a yes/no existence test and duplicates worry you, `EXISTS`
is the safer, clearer choice.

---

## 6. What to do when the match is NOT unique

If the joined table can match multiple rows and you still want a JOIN, de-dup the
output:

**Option A — `DISTINCT`:**

```sql
SELECT DISTINCT news.id, news.title
FROM news
INNER JOIN news_tag ON news_tag.news_id = news.id AND news_tag.tag = 'AAPL.US';
```

**Option B — `GROUP BY`:**

```sql
SELECT news.id, news.title
FROM news
INNER JOIN news_tag ON news_tag.news_id = news.id AND news_tag.tag = 'AAPL.US'
GROUP BY news.id, news.title;
```

**Option C — just use `EXISTS`** (section 5), which never fans out.

For an intersection with counting you might also see:

```sql
SELECT news.id
FROM news_tag
WHERE tag IN ('AAPL.US','earnings')      -- both possible tags
GROUP BY news_id
HAVING COUNT(DISTINCT tag) = 2;          -- ... and the row has BOTH
```

This works but forces a grouping/aggregation step; the self-join or `EXISTS`
forms usually let the database stop earlier and are easier to read.

---

## 7. Cheat sheet

- `INNER JOIN` keeps only left rows that **have a match** → that alone is a filter.
- A join **multiplies** rows when the right side matches more than once (fan-out).
- Push the constant conditions into `ON` (or `WHERE` — same thing for INNER JOIN)
  to filter to specific matches.
- **`INNER JOIN` + a unique key on the join target = a clean filter (no dupes).**
  Without the unique key, add `DISTINCT`/`GROUP BY`, or use `EXISTS`.
- **N joins to the same table = AND / intersection.** `IN (...)` is OR / union —
  don't confuse them.
- Need columns from the match → JOIN. Just a yes/no test → `EXISTS`.

---

## 8. Try it yourself

1. Write a query for "articles tagged `GOOG.US`". (Expected: article 3.)
2. Write a query for "articles that have a `ticker` tag **and** an `earnings`
   label" — for *any* ticker, not a specific one. (Hint: drop the `tag = ...` on
   the ticker join.) Expected: articles 1 and 3.
3. Rewrite exercise 2 using `EXISTS`.
4. Add a second ticker to article 1 (`INSERT INTO news_tag VALUES (1,'ticker','MSFT.US');`)
   then run a query that selects the article joined to *any* ticker tag. Notice
   article 1 now appears twice — fix it with `DISTINCT`.
