# python-therapi
Therapy to ease the pain of writing boilerplate JSON API consumers.

---

Tired of writing the same code to consume JSON APIs, over and over? Let's solve that!

## Query a basic, public JSON API

To query any basic, public JSON API, we create our consumer class and inherit from `BaseAPIConsumer`, as follows:

```python
from therapi import BaseAPIConsumer

class MyAPIConsumer(BaseAPIConsumer):
    base_url = "https://www.an-awesome-service.com/api"
```

Now we can use this class to make API calls to different endpoints, as follows:

```python
consumer = MyAPIConsumer()
result = consumer.json_request(method="get", path="items", params={"id": 123})
print(result)
```

We would see, for example, this response:

```json
{
  "data": [
    {"name": "Laptop", "price": 239},
    {"name": "Printer", "price": 99}
  ]
}
```
