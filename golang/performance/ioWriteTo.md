# How to use golang io.WriterTo 

`io.WriterTo` is a **performance-oriented interface** in Go. It lets a type write itself directly to an `io.Writer`, often **avoiding extra buffering, allocations, or copies**.

---

## 1. What is `io.WriterTo`?

```go
type WriterTo interface {
    WriteTo(w Writer) (n int64, err error)
}
```

If a value implements `WriterTo`, Go’s I/O helpers (like `io.Copy`) will **prefer it automatically**.

---

## 2. Why `WriterTo` exists

Normally data flows like this:

```
Reader → buffer → Writer
```

With `WriterTo`, the object can do:

```
Object → Writer
```

This enables:

* zero-copy or fewer copies
* syscall optimizations (e.g. `sendfile`)
* protocol-aware writing

---

## 3. Basic example: implement `WriterTo`

```go
type Message struct {
    Data []byte
}

func (m *Message) WriteTo(w io.Writer) (int64, error) {
    n, err := w.Write(m.Data)
    return int64(n), err
}
```

Usage:

```go
msg := &Message{Data: []byte("hello")}
io.Copy(os.Stdout, msg) // WriteTo is called automatically
```

---

## 4. `io.Copy` behavior (important)

Internally, `io.Copy(dst, src)` does:

1. If `src` implements `io.WriterTo` → call `src.WriteTo(dst)`
2. Else if `dst` implements `io.ReaderFrom` → call `dst.ReadFrom(src)`
3. Else → fallback buffer loop

So **you usually don’t call `WriteTo` yourself**.

---

## 5. Real-world examples in stdlib

### `bytes.Buffer`

```go
buf := bytes.NewBufferString("hello")
io.Copy(os.Stdout, buf) // uses buf.WriteTo
```

### `bytes.Reader` (zero-copy-ish)

```go
r := bytes.NewReader(data)
io.Copy(conn, r)
```

### `os.File` (platform optimized)

```go
f, _ := os.Open("bigfile")
io.Copy(conn, f) // may use sendfile internally
```

---

## 6. When **you should** implement `WriterTo`

Implement it when:

✅ You control the type
✅ You can write more efficiently than generic copying
✅ You want protocol framing / batching
✅ You want to avoid intermediate buffers

Common use cases:

* HTTP / RPC responses
* file → network streaming
* compressed / encrypted writers
* log batching
* binary protocol encoders

---

## 7. Example: streaming with framing

```go
type FrameWriter struct {
    Payload []byte
}

func (f *FrameWriter) WriteTo(w io.Writer) (int64, error) {
    var total int64

    // length prefix
    if err := binary.Write(w, binary.BigEndian, uint32(len(f.Payload))); err != nil {
        return total, err
    }
    total += 4

    n, err := w.Write(f.Payload)
    total += int64(n)

    return total, err
}
```

Usage:

```go
fw := &FrameWriter{Payload: data}
io.Copy(conn, fw)
```

---

## 8. Common mistakes ❌

### ❌ Calling `WriteTo` manually

```go
fw.WriteTo(w) // usually unnecessary
```

Prefer:

```go
io.Copy(w, fw)
```

---

### ❌ Ignoring partial writes

```go
w.Write(buf) // may write less than len(buf)
```

Correct:

```go
n, err := w.Write(buf)
if n < len(buf) && err == nil {
    err = io.ErrShortWrite
}
```

---

### ❌ Forgetting byte count accuracy

The returned `int64` **must match actual bytes written**, or `io.Copy` may misbehave.

---

## 9. WriterTo vs ReaderFrom

| Interface       | Direction | Typical user      |
| --------------- | --------- | ----------------- |
| `io.WriterTo`   | src → dst | readers / buffers |
| `io.ReaderFrom` | dst ← src | files / sockets   |

If you implement both, Go picks **WriterTo first**.

---

## 10. Rule of thumb

> Implement `io.WriterTo` when your type **knows best how to write itself efficiently**.

If you want, I can:

* show a **benchmark** vs normal `io.Copy`
* explain how HTTP uses `WriterTo`
* design a **zero-copy streaming API** for your backend services

