---
paths:
  - "packages/**/*.py"
---
These instructions OVERRIDE any default behavior and you MUST follow them exactly.

## RULES
- `from __future__ import annotations` at the top of every module
- `X | None` not `Optional[X]`. `list[str]` not `List[str]`. `dict[str, Any]` not `Dict`
- No wildcard imports: `from module import *`
- No `print()` — use `from prolook_mcp_core.log import Log`
- No `os.getenv()` or `os.environ` — use `from prolook_mcp_core.config import settings`
- No `datetime.utcnow()` — use `datetime.now(tz=timezone.utc)`
- Files ≤ 400 lines — split by sub-concern if exceeded
- Max 4 function parameters — use Pydantic model or dataclass if more needed
- No magic numbers — define named constants

## PATTERNS

### Type annotations
```python
from __future__ import annotations
def get_order(order_id: str, ctx: BrandContext) -> dict | None: ...
items: list[str] = []
```

### Pydantic v2
```python
model_config = ConfigDict(...)       # NEVER inner class Config
@model_validator(mode="after")
@field_validator("field", mode="before")
```

### Constants
```python
_BCRYPT_ROUNDS: int = 12
_RATE_LIMIT_WINDOW_SECONDS: int = 60
```

## ANTI-PATTERNS
- `Optional[X]` — use `X | None`
- `from typing import List, Dict` — use built-in generics
- `print(...)` — use `Log.info()`
- `os.getenv(...)` — use `settings.FIELD`
- `except Exception: pass` — always log + handle specifically
- `raise SomeError(...)` without `from exc` — always chain exceptions
