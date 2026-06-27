# In kdb+ q table definition

```
trade:([] 
    time:();
    sym:();
    price:();
    size:()
)
```

why it doesn't need data type


In **kdb+ / q**, table column **types are inferred from the list you assign**, so you often **don’t explicitly declare types** the way you would in SQL or C-like languages.

Your definition:

```q
trade:([] 
    time:();
    sym:();
    price:();
    size:()
)
```

works because **`()` means an empty list**, and in **q an empty list has a default type**. When used in table construction, q will infer a **generic empty list**, and the column type will be finalized when you first insert data.

---

## 1. What `([] ...)` means

In q:

```
([] col1:list1; col2:list2)
```

means **create a table with columns backed by lists**.

So your code means:

```
trade table
 ├─ time  : list
 ├─ sym   : list
 ├─ price : list
 └─ size  : list
```

Each column is initially an **empty list**.

---

## 2. Type is determined by the first insert

Example:

```q
trade insert (`time`sym`price`size)!(10:00:00.000;`AAPL;100.5;200)
```

After this insert, q infers:

| column | type   |
| ------ | ------ |
| time   | time   |
| sym    | symbol |
| price  | float  |
| size   | int    |

Because q is **strongly typed but dynamically inferred**.

---

## 3. Professional kdb+ code usually *does* specify types

In production (especially trading systems), people usually define types explicitly to avoid mistakes:

```q
trade:([] 
    time:`time$();
    sym:`symbol$();
    price:`float$();
    size:`int$()
)
```

or the shorter idiom:

```q
trade:([] time:`time$(); sym:`symbol$(); price:`float$(); size:`int$())
```

Now the schema is **fixed immediately**.

---

## 4. Why q allows this design

q tables are basically:

```
table = dictionary(columnName -> columnVector)
```

So:

```
trade
= `time`sym`price`size!
  (timeList; symList; priceList; sizeList)
```

Because lists carry their own type, **column type = list type**.

---

## 5. SQL vs q philosophy

| SQL           | q                        |
| ------------- | ------------------------ |
| schema-first  | data-first               |
| explicit type | inferred from vector     |
| row storage   | column vector storage    |
| INSERT row    | append to column vectors |

This is why **kdb+ can append millions of rows extremely fast**.

---

✅ **Key takeaway**

Your table works without types because:

```
q column type = type of the underlying list
```

and `()` is simply an **empty list whose type will be resolved later**.

---

If you're learning **kdb+ for trading systems**, I can also show the **5 canonical ways professionals define table schemas**, which are much faster and safer than this beginner style.
