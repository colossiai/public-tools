# Index condition

In MySQL, **Index Condition Pushdown (ICP)** is an optimization technique used to improve query performance by reducing the number of rows that need to be fetched from the storage engine. It allows MySQL to filter rows at the storage engine level, where the index is scanned, rather than at the MySQL server layer. This is particularly useful in queries that involve **range scans** on indexes.

### **How it works:**

When a query is executed, MySQL often needs to scan an index to locate rows that match the query's conditions. Without ICP, MySQL fetches rows from the storage engine, then evaluates the full set of query conditions at the server level. With ICP enabled, part of the query condition can be evaluated during the index scan itself, filtering out rows early, which reduces the amount of data passed to the server.

### **Example:**

Suppose you have a table users with an index on the columns age and city:

sql

Copy code

SELECT \* FROM users WHERE age \> 30 AND city = 'New York';

- Without ICP: MySQL would use the index on age, retrieve all rows where age \> 30, and then filter out rows where city is not 'New York' at the server level.

- With ICP: **MySQL pushes both conditions (age \> 30 and city = 'New York') down to the storage engine,** allowing the filtering to happen at the index level. This reduces the number of rows returned to the server for further processing.

### **Benefits:**

- **Reduced Disk I/O**: By filtering rows at the storage engine, fewer rows need to be read from disk.

- **Improved Query Performance**: By processing rows earlier in the query execution, overall execution time is reduced.

### **When ICP is Used:**

ICP is typically used when:

- There are multiple conditions in a WHERE clause.

- The conditions involve indexed columns.

- The query includes range scans on indexes.

In summary, "index condition" refers to the conditions MySQL evaluates during an index scan, and "Index Condition Pushdown" is the optimization that allows MySQL to push those conditions closer to the data source for more efficient filtering.
