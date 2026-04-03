# #Why json.Unmarshal can't convert "hello" into string variable?

`json.Unmarshal` **can** convert `"hello"` into a Go `string`. The problem usually happens when the JSON input is not actually a JSON string.

### Correct example

```go
package main

import (
	"encoding/json"
	"fmt"
)

func main() {
	var s string
	err := json.Unmarshal([]byte(`"hello"`), &s)
	if err != nil {
		panic(err)
	}
	fmt.Println(s)
}
```

Output:

```
hello
```

Important detail:

* JSON string → **must include quotes** `"hello"`
* Go string variable → `string`

---

### Common mistake

If you try:

```go
var s string
json.Unmarshal([]byte(`hello`), &s)
```

You will get an error like:

```
invalid character 'h' looking for beginning of value
```

because `hello` is **not valid JSON**.

Valid JSON values must be one of:

* `"string"`
* `123`
* `true`
* `false`
* `null`
* `{...}`
* `[...]`

So `"hello"` is valid JSON, but `hello` is not.

---

### Another common issue: type mismatch

Example:

```go
var s string
json.Unmarshal([]byte(`123`), &s)
```

Error:

```
json: cannot unmarshal number into Go value of type string
```

Go's JSON decoder is **strict about types**.

---

### Rule of thumb

| JSON value | Go type           |
| ---------- | ----------------- |
| `"hello"`  | `string`          |
| `123`      | `int` / `float64` |
| `true`     | `bool`            |
| `{}`       | `struct` / `map`  |
| `[]`       | `slice`           |

---

### Production debugging trick

When unsure what JSON you're receiving:

```go
var v any
json.Unmarshal(data, &v)
fmt.Printf("%T %v\n", v, v)
```

This shows the actual JSON type.

---

If you want, I can also show a **very common backend bug** where `json.Unmarshal` fails when the JSON field sometimes returns `"string"` and sometimes `123` (APIs do this a lot) and how production Go code handles it cleanly.
