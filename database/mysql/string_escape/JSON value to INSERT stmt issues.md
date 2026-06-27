# Convet JSON value to Mysql INSERT issues

## Requirement

Convert `orig_lang.cfg.json` into SQL INSERT statements for the `lang_config` table.

The original JSON structure:
```json
{
  "data": {
    "languages": {
      "en-US": { "key": "value", ... },
      "zh-TW": { "key": "value", ... },
      "zh-CN": { "key": "value", ... }
    }
  }
}
```

Each language's entire key-value object should be inserted as a single row, with `lang` as the language code and `content` as the full JSON string.

Target table schema:
```sql
CREATE TABLE `lang_config` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `lang` varchar(20) NOT NULL,
  `content` text NOT NULL,
  ...
);
```

## Issues

### Issue 1: Backslash escaping — invalid JSON stored in MySQL

**Symptom:** Go's `json.Unmarshal` failed with: `invalid character '\n' in string literal`.

**Cause:** The JSON content contains escape sequences like `\n` (newlines in multi-line text) and `\"` (double quotes) inside string values. MySQL's default string handling interprets backslashes as escape characters in single-quoted strings:

| In SQL string | MySQL stores | Expected |
|---|---|---|
| `\n` | actual newline (0x0A) | `\n` (two chars) |
| `\"` | `"` | `\"` (two chars) |

This silently corrupted the JSON, making it invalid.

**Solution:** Double every backslash before embedding JSON into SQL strings:

```python
# Before (broken)
escaped = json_str.replace("'", "''")
# output INSERT .. VALUES '{"title":"Welcome","desc":"Promotion description, \n\"good offer\"\nCome with friends!!"}'

# After (fixed)
escaped = json_str.replace('\\', '\\\\').replace("'", "''")
# output INSERT .. VALUES '{"title":"Welcome","desc":"Promotion description, \\n\\"good offer\\"\\nCome with friends!!"}'
```



This ensures:
- `\n` → `\\n` in SQL → MySQL stores `\n` (valid JSON)
- `\"` → `\\"` in SQL → MySQL stores `\"` (valid JSON)
