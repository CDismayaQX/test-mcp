"""Seed a Riddell dev brand + API key for local testing.

Prints the full API key once — it is not stored in plaintext anywhere.
Run: uv run python scripts/seed_dev_brand.py
"""

from __future__ import annotations

import asyncio
import secrets
import uuid

import asyncpg
import bcrypt

_DB_DSN = "postgresql://postgres:postgres@localhost:5433/ai_assistant_dev"
_BCRYPT_ROUNDS: int = 12
_ENV = "local"
_BRAND_SLUG = "riddell"
_BRAND_NAME = "Riddell"


async def main() -> None:
    conn = await asyncpg.connect(_DB_DSN)

    # Upsert brand
    brand_id = str(uuid.uuid4())
    existing = await conn.fetchval("SELECT id FROM brands WHERE slug = $1", _BRAND_SLUG)
    if existing:
        brand_id = str(existing)
        print(f"Brand '{_BRAND_SLUG}' already exists — id={brand_id}")
    else:
        await conn.execute(
            "INSERT INTO brands (id, slug, name, status) VALUES ($1, $2, $3, 'active')",
            uuid.UUID(brand_id),
            _BRAND_SLUG,
            _BRAND_NAME,
        )
        print(f"Created brand '{_BRAND_SLUG}' — id={brand_id}")

    # Generate API key
    random_part = secrets.token_hex(16)
    full_key = f"pk_{_ENV}_{_BRAND_SLUG}_{random_part}"
    key_prefix = full_key.rsplit("_", 1)[0]  # pk_local_riddell
    key_hash = bcrypt.hashpw(full_key.encode(), bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()

    await conn.execute(
        """
        INSERT INTO brand_api_keys
            (id, brand_id, key_prefix, key_hash, environment, rate_limit_per_minute, status)
        VALUES ($1, $2, $3, $4, $5, 100, 'active')
        """,
        uuid.uuid4(),
        uuid.UUID(brand_id),
        key_prefix,
        key_hash,
        _ENV,
    )

    await conn.close()

    print()
    print("=" * 60)
    print(f"  Brand slug : {_BRAND_SLUG}")
    print(f"  Key prefix : {key_prefix}")
    print(f"  Full key   : {full_key}")
    print("=" * 60)
    print()
    print("Use this header to test the brand server:")
    print(f"  Authorization: Bearer {full_key}")


asyncio.run(main())
