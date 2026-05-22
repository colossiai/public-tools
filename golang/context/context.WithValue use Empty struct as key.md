# #Explain go idiom: type fooKey struct{} + ctx.Value(fooKey{})

This is a common Go idiom for storing/retrieving values in a `context.Context` using a **private, unique key type**.

Example:

```go
type fooKey struct{}

ctx = context.WithValue(ctx, fooKey{}, "hello")

v := ctx.Value(fooKey{})
fmt.Println(v) // hello
```

## Why use `struct{}` as the key?

The problem being solved is **key collision**.

Bad example:

```go
ctx = context.WithValue(ctx, "user_id", 123)
```

Later, another package might also use `"user_id"`:

```go
ctx = context.WithValue(ctx, "user_id", 456)
```

Now values collide.

Instead, Go idiom is:

```go
type fooKey struct{}
```

This creates a **distinct type**.

Then:

```go
fooKey{}
```

creates a zero-value instance of that type.

Because key equality in Go depends on both **type + value**, this key is unique.

For example:

```go
type fooKey struct{}
type barKey struct{}

fmt.Println(fooKey{} == fooKey{}) // true
fmt.Println(fooKey{} == barKey{}) // compile error
```

Even though both are empty structs, they are different types.

So:

```go
ctx.Value(fooKey{})
```

will only match values stored using exactly the same key type.

---

## Why `struct{}` specifically?

```go
struct{}
```

is an **empty struct**:

```go
type fooKey struct{}
```

Reasons:

1. **Zero-size allocation**

Empty struct occupies 0 bytes.

```go
unsafe.Sizeof(struct{}{}) // 0
```

2. **No data needed**

The type identity matters, not the content.

You're using it like a namespace token.

3. **Cheap singleton-ish value**

This:

```go
fooKey{}
```

always represents the same empty value.

---

## How lookup works

When you do:

```go
ctx = context.WithValue(ctx, fooKey{}, 123)
```

internally it's conceptually like:

```go
map[any]any{
    fooKey{}: 123,
}
```

Then:

```go
ctx.Value(fooKey{})
```

works because:

```go
fooKey{} == fooKey{}
```

is `true`.

But this won't work:

```go
type fooKey2 struct{}

ctx.Value(fooKey2{}) // nil
```

Different type.

---

## Why define a type instead of variable?

You may also see:

```go
type contextKey string

const userIDKey contextKey = "user_id"

ctx = context.WithValue(ctx, userIDKey, 123)
```

or:

```go
var userKey = struct{}{}
```

But the `type fooKey struct{}` pattern is preferred for package-private keys because it avoids accidental collisions and keeps intent clear.

Typical production pattern:

```go
package auth

type userKey struct{}

func WithUser(ctx context.Context, user *User) context.Context {
    return context.WithValue(ctx, userKey{}, user)
}

func UserFromContext(ctx context.Context) (*User, bool) {
    user, ok := ctx.Value(userKey{}).(*User)
    return user, ok
}
```

Notice callers never touch the key directly.

They use helper functions, which hides implementation details and keeps type safety localized.

You can think of `fooKey{}` as a **unique invisible label** attached to the context.
