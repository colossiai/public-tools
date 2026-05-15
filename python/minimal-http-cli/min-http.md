# #Minimal example to send http get request in python


Using only Python standard library (`urllib.request`):

```python
from urllib.request import urlopen

url = "https://httpbin.org/get"

with urlopen(url) as resp:
    body = resp.read().decode("utf-8")

print(body)
```

With headers:

```python
from urllib.request import Request, urlopen

req = Request(
    "https://httpbin.org/get",
    headers={
        "User-Agent": "my-app/1.0",
    },
)

with urlopen(req) as resp:
    print(resp.status)
    print(resp.read().decode())
```

JSON example:

```python
import json
from urllib.request import urlopen

with urlopen("https://httpbin.org/json") as resp:
    data = json.load(resp)

print(data)
```
