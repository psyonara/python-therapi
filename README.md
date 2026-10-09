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

---

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency management,
virtual environments, running tools, and building packages. Install it once
per machine (see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)).

```console
$ uv sync                        # create/refresh .venv, install the project + dev group
$ uv run pytest                  # run the test suite
$ uv run ruff check              # lint
$ uv run mypy therapi            # type-check
$ uv build                       # build sdist + wheel
$ uv publish                     # upload to PyPI
```

The Python version is pinned in [`.python-version`](.python-version); the
lockfile ([`uv.lock`](uv.lock)) is committed for reproducible environments.
