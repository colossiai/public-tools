# **Unique order**

# I have a API service that will accept user order, the order will be saved in t_order table (mysql), user need to input (user_id, symbol, tag), how can I ensure that (user_id, symbol, tag) is unique when accepting request in API service? if not the API service will reject the order.

# 

To ensure that the combination (user_id, symbol, tag) is unique when accepting an order via your API service, you should **enforce uniqueness at both the database level and the application level**. Here's how to do both:

### **✅ 1. Enforce Uniqueness in the Database (MySQL)**

In your t_order table, create a **unique composite index** on the three columns:

ALTER TABLE t_order ADD UNIQUE KEY uniq_user_symbol_tag (user_id, symbol, tag);

This ensures that **no duplicate entries can be inserted**, even in case of concurrent API calls or bypassed logic.

### **✅ 2. Handle Duplicate Gracefully in API Service (Application Level)**

In your API service (assuming you're using a language like Go, Python, or Node), **before inserting**, you can:

- **<span class="mark">Option A (RECOMMENDED): Try inserting directly and catch the unique constraint violation error.  
  </span>**

- **Option B:** Check first (read), then insert (write) — but this has a **race condition** risk unless done in a transaction with proper isolation or with database lock (not ideal for high performance systems).

### **✅ Example Using Option A: Insert and Catch Error (Go Example)**

\_, err := db.Exec(\`

INSERT INTO t_order (user_id, symbol, tag)

VALUES (?, ?, ?)\`, userID, symbol, tag)

if err != nil {

if strings.Contains(err.Error(), "Duplicate entry") {

return errors.New("duplicate order: same (user_id, symbol, tag) already exists")

}

return err // other DB errors

}

This is **safe and simple**, because the database is the source of truth.

### **✅ Summary**

| **Layer**     | **Strategy**                             |
|---------------|------------------------------------------|
| **Database**  | Unique index on (user_id, symbol, tag)   |
| **App Logic** | Catch insert errors (on duplicate entry) |

Do you want example code for a specific language like Go, Node.js, or Python?
