# Give me Chrome console fetch() commands

Here’s a basic **`fetch()`** you can paste straight into the Chrome DevTools console 👇

**Simple GET request**

```js
fetch('https://api.example.com/data').then(res => res.json()).then(data => console.log(data)).catch(err => console.error(err));
```

**GET with headers**

```js
fetch('https://api.example.com/data', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Accept': 'application/json'
  }
})
  .then(res => res.json())
  .then(console.log);
```

**POST request (JSON body)**

```js
fetch('https://api.example.com/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'Alice',
    age: 30
  })
})
  .then(res => res.json())
  .then(console.log);
```

**Quick one-liner (good for testing)**

```js
await fetch('https://api.example.com/data').then(r => r.text())
```

*(Works if the console is in an async context — Chrome supports this.)*

If you tell me what endpoint you’re hitting (auth, cookies, CORS, form data, etc.), I’ll tailor it exactly.
