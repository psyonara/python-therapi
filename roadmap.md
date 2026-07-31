# Roadmap: `python-therapi` 0.0.4 → 1.0.0

Therapy to ease the pain of writing boilerplate JSON API consumers.

This document records the agreed path from the current pre-release state
(0.0.4, dormant since May 2023) to a production-ready 1.0.0.

## Locked-in decisions

- **Sync-only** (`requests`) for 1.0 — async support is deferred to a
  post-1.0 candidate.
- **Python `^3.11`** floor — drops EOL'd 3.8/3.9/3.10 and unlocks
  modern typing ergonomics.
- **No response models** in 1.0 — endpoints return raw JSON
  (dict/list). Pydantic/dataclass integration is a post-1.0 candidate.
- **`uv`** replaces Poetry for dependency management, locking,
  virtualenvs, running, and package building — one fast Rust tool,
  PEP 621 `pyproject.toml`, committed `uv.lock`.
- A first-class **plugin framework** generalizes the existing
  `RequestModifier` / `ResponseModifier` pair into lifecycle-aware
  plugins; the built-in modifiers ship as plugins (see §2.9).
- 1.0 keeps the existing modifier-based architecture; nothing is
  rewritten from scratch.

---

## Known issues to resolve (in priority order)

| #  | File:line                       | Issue                                                                   |
| -- | ------------------------------- | ----------------------------------------------------------------------- |
| 1  | `therapi/base.py`               | ~~Mutable class-level list defaults~~ — fixed (instance attrs, `None` defaults) ✓ |
| 2  | `therapi/base.py`               | ~~`construct_url` mutates caller's `params`~~ — fixed (local copy) ✓    |
| 3  | `therapi/__init__.py`           | ~~`import *` at bottom~~ — fixed (pure re-export from `base.py`) ✓      |
| 4  | `therapi/authentication.py`     | ~~`AuthenticationError` never raised~~ — fixed (guards in auth ctors) ✓ |
| 5  | `therapi/base.py`               | ~~No request timeout~~ — fixed (instance `timeout=30.0`, passed to `requests`) ✓ |
| 6  | `examples/thingiverse/`         | ~~Example shipped inside package~~ — moved out of `therapi/` ✓         |
| 7  | repo                            | Zero tests — pytest is a dev dep but unused *(open — deferred subset)* |
| 8  | repo                            | No CI, no lint, no type-check, no `py.typed` *(open — deferred subset)* |
| 9  | `pyproject.toml`                | `python = "^3.8"` — 3.8 EOL; also `list[X]` in code needs ≥3.9 *(open)* |
| 10 | `therapi/modifiers.py`          | ~~`LoggingModifier` logs raw headers~~ — fixed (`redact_headers`) ✓     |

---

## Phase 1 — Stabilize → `0.1.0`

*Make the existing code correct, tested, typed, and safe to depend on.*

### 1.1 Restructure the package (no functional changes for users)

> Starting point: the uncommitted modifier-refactor diff had already
> split auth into `therapi/authentication.py` and built-in modifiers
> into `therapi/modifiers.py`, and introduced the `import *` hack at
> the bottom of `__init__.py` to surface them. This pass therefore
> relocates the core four symbols (`Endpoint`, `BaseAPIConsumer`,
> `RequestModifier`, `ResponseModifier`) into `therapi/base.py` and
> turns `__init__.py` into a pure re-export surface, retiring the
> `import *` hack. The modifiers/auth submodules now import from
> `therapi.base` (no circular `import therapi`).

- Move `Endpoint`, `BaseAPIConsumer`, `RequestModifier`,
  `ResponseModifier` from `therapi/__init__.py` into `therapi/base.py`.
- `therapi/__init__.py` becomes a pure re-export surface:

  ```python
  from therapi.base import BaseAPIConsumer, Endpoint, RequestModifier, ResponseModifier
  from therapi.authentication import (
      TokenBearerAuthentication,
      APIKeyAuthentication,
      BasicAuthentication,
  )
  from therapi.modifiers import (
      UserAgentModifier,
      LoggingModifier,
      HeaderModifier,
      PaginationModifier,
      ResponseTransformModifier,
  )
  from therapi.exceptions import (
      TherapiError,
      HTTPStatusError,
      TimeoutError,
      AuthenticationError,
  )
  ```

- Eliminates the `import *` hack at the bottom of `__init__.py` (#3).

### 1.2 Move the example out of the package (#6)

- Move `therapi/thingipy.py` → `examples/thingiverse/thingiverse_client.py`.
- Certify `therapi/` contains only library code.

### 1.3 Fix correctness bugs

- `therapi/base.py`:
  - `request_modifiers: list | None = None` (class attr) and
    `request_modifiers or []` in `__init__`; never use a mutable class
    default (#1).
  - `construct_url` operates on `params = dict(params or {})` (copy) and
    does not modify the caller's dict — leftover params are returned or
    carried internally — no caller-side side effects (#2).
- `therapi/authentication.py`: raise `AuthenticationError` when
  `token` / `api_key` is empty or `None`, at construction or at
  `modify_headers` time (#4).
- `therapi/base.py` `json_request`: pass `timeout=self.timeout` (instance
  default, e.g. 30s, overridable per call) (#5).
- `LoggingModifier`: add `redact_headers=("Authorization", "X-API-Key",
  ...)` kwarg; replace redacted values with `<redacted>` before logging
  (#10).

### 1.4 Switch to `uv` (drop Poetry)

The project currently uses Poetry (`[tool.poetry]`, `poetry.lock`,
`poetry-core` build backend). Migrate to `uv` for a single, fast Rust
tool covering venvs, resolution, locking, running, and building.

- Convert `pyproject.toml` from the Poetry schema to PEP 621 standard:
  - `[project]` table with `name`, `version`, `description`, `readme`,
    `license`, `requires-python`, `authors`, `dependencies`,
    `classifiers`.
  - `[dependency-groups]` for dev tooling (`pytest`, `ruff`, `mypy`,
    `responses`, `pytest-cov`).
  - Build backend switches from `poetry-core` to `hatchling` (standard,
    pure-Python wheel, no Poetry dependency at build time).
  - Remove all `[tool.poetry.*]` tables.
- Replace `poetry.lock` with `uv.lock`, committed for reproducible CI.
- Add a `.python-version` pin (e.g. `3.11`) so local dev and CI agree.
- Adopt the `uv` developer workflow:
  - `uv sync` — create/refresh the venv, install the project + dev group.
  - `uv run pytest` / `uv run ruff check` / `uv run mypy therapi`.
  - `uv build` — produce sdist + wheel.
  - `uv publish` — upload to PyPI (trusted publishing / API token).
- Update `CONTRIBUTING.md` (§1.9) and the README quickstart to show
  `uv` commands.
- Delete `poetry.lock` and Poetry config from the repo once CI is green
  on `uv`.

### 1.5 Set Python floor `^3.11` (#9)

- `pyproject.toml` (`[project]`): `requires-python = ">=3.11"`.
- Add dev deps under the `dev` dependency group: `pytest = ">=8,<9"`,
  `responses = ">=0.25"`, `ruff = ">=0.6"`, `mypy = ">=1.11"`,
  `pytest-cov`.

### 1.6 Type the library and ship `py.typed` (#8)

- Add `therapi/py.typed` (empty marker file).
- Type-annotate every public symbol; use `list[RequestModifier]` not
  bare `list` (the 3.11 floor makes this clean).
- Enable `mypy --strict` (or a curated strict subset) in CI.

### 1.7 Tests (zero → comprehensive) (#7)

Layout under `tests/` mirroring `therapi/`:

```
tests/
  conftest.py            # fixtures: mock server via `responses`
  test_construct_url.py
  test_json_request.py
  test_call_endpoint.py
  test_modifiers.py
  test_authentication.py
  test_logging_redaction.py
  test_errors.py
  test_session_lifecycle.py   # added in Phase 2
```

Coverage target: ≥ 90% on `therapi/`.

### 1.8 Initial CI scaffolding (#8)

- `.github/workflows/ci.yml`: matrix Python `3.11 / 3.12 / 3.13`;
  install via `uv` using the `astral-sh/setup-uv@v3` action (pin the
  action version); run `uv run ruff check`, `uv run mypy therapi`,
  `uv run pytest`.
- `.github/workflows/release.yml`: build wheels with `uv build`,
  publish to TestPyPI on tag (gated), using trusted publishing (OIDC)
  where possible.

### 1.9 Repo hygiene

- Remove tracked `dist/` artifacts from the working tree (they are
  gitignored already); optionally scrub from history later if
  convenient.
- Add `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and issue/PR
  templates.

### 1.10 Release `0.1.0`

Tag, GitHub Release, publish to PyPI.

---

## Phase 2 — Modernize & Harden → `0.2.0`

*Feature parity with what a 2026 API client user expects — still sync.*

### 2.1 Session reuse

- `BaseAPIConsumer` owns a `requests.Session` (connection pooling,
  cookie jar, persistent headers).
- Add `close()` and `__enter__` / `__exit__` for
  `with MyConsumer() as c:` usage.

### 2.2 Error model

Replace raw `requests.HTTPError` propagation with typed exceptions:

```
TherapiError                      # base
├── TransportError                # network / connection
├── TimeoutError                  # request or connect timeout
├── AuthenticationError           # 401/403 or bad creds
├── HTTPStatusError               # 4xx/5xx not handled by auth
│   .status_code, .response, .url
└── ValidationError               # local param validation
```

Catch `requests.RequestException` inside `json_request` and translate.

### 2.3 Retry / backoff

New `RetryModifier(RequestModifier)` with:

- max attempts, exponential backoff + jitter
- retryable status allowlist (default `{429, 502, 503, 504}`)
- respect the `Retry-After` header
- cap on total wall time

Pluggable: users compose it with their other modifiers; not hard-wired
into `json_request`.

### 2.4 Pagination iterator

> Note: the in-repo `PaginationModifier` (§1.1) is a **low-level param
> injector** only — it adds `page` / `per_page` keys to the request
> params. The strategy-driven *iterator* described here is a separate
> Phase-2 `PaginationPlugin` (see §2.9), which builds on and supersedes
> that modifier; the two should not be conflated.

- `Paginator` class plus `BaseAPIConsumer.iter_paginated(endpoint, ...)`
  returning an `Iterator[dict | list]`.
- Built-in strategies (selectable per call): `link-header`,
  `page+per_page`, `cursor`.
- Strategy interface is subclassable for exotic APIs.

### 2.5 More auth

- `BasicAuthentication(username, password)`.
- `OAuth2ClientCredentialsAuthentication(token_url, client_id,
  client_secret, scopes)` — auto-fetch and refresh bearer token;
  thread-safe token cache with TTL.

### 2.6 Configurable timeouts & sizes

- `BaseAPIConsumer(base_url, timeout=..., connect_timeout=...,
  read_timeout=...)`.
- Per-call override in `json_request(..., timeout=...)`.

### 2.7 Observability

- `LoggingModifier` already redacts (Phase 1); make verbosity levels
  configurable: `request_summary`, `request_headers`, `request_body`,
  `response_summary`, `response_body` — flags off by default.
- Optional `StatsdModifier` placeholder (interface only; implementation
  later).

### 2.8 Parser-friendly responses

- `call_endpoint(..., raw=False)` returns parsed JSON; `raw=True`
  returns the `requests.Response` for edge cases (streaming downloads,
  non-JSON endpoints).
- Add `download(url, dest)` and `iter_stream(url)` helpers for
  binary/streaming.

### 2.9 Plugin framework

The existing `RequestModifier` / `ResponseModifier` pair is a narrow
plugin shape limited to mutating a single request/response. Generalize
into a first-class plugin system so third parties can ship
`therapi-*` packages that add capabilities (caching, telemetry,
custom auth, rate limiting, …) without touching the core.

**Plugin contract**

```python
class Plugin:
    name: str
    priority: int = 100                 # lower runs first; ties broken by name

    def configure(self, config: Mapping[str, Any]) -> None: ...

    # Optional lifecycle hooks (omit the ones you don't need):
    def on_request(self, ctx: RequestContext) -> None: ...
    def on_response(self, ctx: ResponseContext) -> None: ...
    def on_error(self, ctx: ErrorContext) -> bool | None: ...   # True => recovered

    # Bridge to the existing modifier pipeline (optional):
    def build_request_modifier(self) -> RequestModifier | None: ...
    def build_response_modifier(self) -> ResponseModifier | None: ...
```

`RequestContext`, `ResponseContext`, `ErrorContext` are dataclasses
carrying the request, response, exception, plus a per-call `state`
dict so plugins can share data across hooks (e.g. a correlation id
set in `on_request` and read in `on_response`).

**Discovery & wiring**

- Entry-point group `therapi.plugins` (PEP 621 / `importlib.metadata`):
  third-party packages expose their plugin classes here.
- Explicit wiring: `BaseAPIConsumer(plugins=[MyPlugin(), ...])`.
- Auto-loading: `therapi.plugins.load_plugins(allowlist=["auth",
  "retry", ...])` discovers installed entry-points; an `allowlist` is
  required for security (no blind auto-activation).
- Ordering by `priority` then `name` is deterministic and documented.

**Backward compatibility**

`RequestModifier` / `ResponseModifier` stay as the low-level
primitives; `Plugin` is the higher-level, lifecycle-aware wrapper.
Modifiers are **instance-based** — constructed with their config
(```TokenBearerAuthentication(token=...)```,
```HeaderModifier({...})```) and passed in
`request_modifiers=[...]` / `response_modifiers=[...]` — they are no
longer class-based with a shared `context` dict. Existing
instance-based subclassers keep working unchanged; new code targets
`Plugin`. Each built-in modifier (Phase 1) gets a thin `Plugin`
adapter so users can adopt the new API piecemeal.

**Built-in plugins to ship in 1.0**

The features in §2.1–§2.8 are delivered *as* plugins; the table maps
each built-in plugin to the feature it realizes.

| Plugin                                | Hooks                                          | Built on (§)             | Notes                                                         |
| ------------------------------------- | ---------------------------------------------- | ------------------------ | ------------------------------------------------------------- |
| `BearerTokenPlugin`                   | `build_request_modifier`                       | `TokenBearerAuthentication` (existing) | raises `AuthenticationError` on empty token (§1.3) |
| `APIKeyPlugin`                        | `build_request_modifier`                       | `APIKeyAuthentication` (existing)     | configurable header field                         |
| `BasicAuthPlugin`                     | `build_request_modifier`                       | §2.5                     | username / password                                           |
| `OAuth2ClientCredentialsPlugin`       | `build_request_modifier`, `on_error`           | §2.5                     | auto token fetch + refresh on 401                            |
| `UserAgentPlugin`                     | `build_request_modifier`                       | `UserAgentModifier` (existing)         |                                                   |
| `HeaderPlugin`                        | `build_request_modifier`                       | `HeaderModifier` (existing)           | arbitrary headers                                  |
| `LoggingPlugin`                       | `on_request`, `on_response`, `on_error`       | `LoggingModifier` (existing)          | redacts sensitive headers (§1.3); verbosity flags (§2.7) |
| `RetryPlugin`                         | `on_error`, `on_request`                       | §2.3                     | backoff + `Retry-After`                                       |
| `PaginationPlugin`                     | `on_response`                                  | §2.4                     | strategy-driven iterator; builds on the low-level `PaginationModifier` (param injection) |
| `ResponseTransformPlugin`             | `build_response_modifier`                      | `ResponseTransformModifier` (existing) | mapping-based reshape                             |
| `ETagCachePlugin`                     | `on_request`, `on_response`                    | new                      | conditional GETs via `If-None-Match`; in-memory cache          |
| `RateLimitPlugin`                     | `on_request`                                   | new (simple)             | client-side politeness delay; full token-bucket is post-1.0  |

Later releases can ship additional plugins (e.g. `SentryPlugin`,
`OpenTelemetryPlugin`, `SignaturePlugin` for HMAC-signed requests) as
separate `therapi-*` packages using the same entry-point group.

### 2.10 Release `0.2.0`

---

## Phase 3 — Documentation & Polish → `1.0.0`

### 3.1 Docs site

- `mkdocs` + `mkdocstrings[python]` material theme, GitHub Pages.
- Pages: quickstart, `BaseAPIConsumer`, `Endpoint`, modifiers, auth,
  pagination, retry, error handling, migration from raw `requests`,
  cookbook.
- API reference auto-generated from docstrings.

### 3.2 README overhaul

- Install line, 30-line quickstart, feature matrix, badges (CI,
  coverage, PyPI, license), comparable-alternatives note, link to the
  docs site.

### 3.3 CHANGELOG semver discipline

(Started in Phase 1.)

- Keep `CHANGELOG.md` under Keep-a-Changelog format.
- CI checks that an entry exists on every PR touching `therapi/`.

### 3.4 CI/CD hardened

- Matrix on Python `3.11 / 3.12 / 3.13`.
- `pip-audit` step for vuln scan; `dependabot` config.
- `pytest --cov=therapi --cov-fail-under=90`.
- Build wheels for `sdist + pure-python wheel`.
- Release workflow: TestPyPI on tag, PyPI on GitHub Release marked
  "published".

### 3.5 Community

- `CONTRIBUTING.md` (dev setup, test, lint commands, PR expectations).
- `CODE_OF_CONDUCT.md`.
- Issue templates: `bug.yml`, `feature.yml`; PR template.
- `SECURITY.md` with disclosure email and SLA.

### 3.6 Final cleanup

- Remove `.idea/` from history if not too disruptive (or leave; it is
  gitignored).
- Confirm `dist/` artifacts are untracked.
- `LICENSE` referenced in `pyproject.toml` already good.

### 3.7 Release `1.0.0`

Tag, GitHub Release notes compiled from CHANGELOG, PyPI publish,
announce (Reddit r/Python, PyPI feed, project README on GitHub profile).

---

## Post-1.0 candidates (deferred, not committed)

- Async backend via `httpx` (since 1.0 stays sync-only).
- Response-model integration (pydantic v2 or stdlib dataclasses).
- OpenAPI-spec → `BaseAPIConsumer` codegen CLI.
- Rate-limit-aware `RateLimitPlugin` upgrade to a real token bucket
  per host.
- Additional `therapi-*` plugins: `SentryPlugin`,
  `OpenTelemetryPlugin`, `SignaturePlugin` (HMAC-signed requests).

---

## Suggested first execution chunk (Phase 1)

Recommended order when picking up implementation:

1. Restructure into `base.py` + clean `__init__.py` (#3)
2. Switch to `uv` + bump Python floor to `^3.11` (§1.4, §1.5, #9)
3. Fix mutable defaults + `construct_url` copy (#1, #2)
4. Move `thingipy.py` → `examples/` (#6)
5. Add tests for current behavior (golden tests before refactor) (#7)
6. Add timeouts + redaction (#5, #10)
7. Type everything + ship `py.typed` (#8)
8. Add CI + lint + mypy (using `uv run …`) (#8)
9. Tag `0.1.0`

This sequence delivers a clean, de-risked base before any new features
land in Phase 2.