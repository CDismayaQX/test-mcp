from __future__ import annotations

from unittest.mock import AsyncMock, patch

import bcrypt
import pytest
from brand_server.auth import (
    _lookup_prefix,
    key_prefix,
    resolve_brand_context,
    verify_api_key,
)
from brand_server.db import BrandKeyRecord
from prolook_mcp_core.errors import InvalidAPIKeyError

_BCRYPT_ROUNDS: int = 4  # fast rounds for tests only


def _make_record(
    brand_id: str = "riddell",
    status: str = "active",
    presented_key: str = "riddell_prod_testkey123",
) -> BrandKeyRecord:
    key_hash = bcrypt.hashpw(presented_key.encode(), bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()
    return BrandKeyRecord(
        brand_id=brand_id,
        brand_name="Riddell",
        key_hash=key_hash,
        rate_limit_per_minute=100,
        status=status,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_key_prefix_returns_first_eight_chars() -> None:
    assert key_prefix("abcdefghijklm") == "abcdefgh"


def test_key_prefix_empty_string_returns_empty() -> None:
    assert key_prefix("") == ""


def test_lookup_prefix_splits_at_last_underscore() -> None:
    assert _lookup_prefix("riddell_prod_secret") == "riddell_prod"


def test_lookup_prefix_no_underscore_returns_whole_key() -> None:
    assert _lookup_prefix("noseparator") == "noseparator"


def test_verify_api_key_valid_returns_true() -> None:
    key = "riddell_prod_abc123"
    stored = bcrypt.hashpw(key.encode(), bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()
    assert verify_api_key(key, stored) is True


def test_verify_api_key_wrong_key_returns_false() -> None:
    key = "riddell_prod_abc123"
    stored = bcrypt.hashpw(b"different_key", bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()
    assert verify_api_key(key, stored) is False


def test_verify_api_key_none_key_returns_false() -> None:
    assert verify_api_key(None, "somehash") is False


def test_verify_api_key_none_hash_returns_false() -> None:
    assert verify_api_key("somekey", None) is False


# ---------------------------------------------------------------------------
# resolve_brand_context
# ---------------------------------------------------------------------------


async def test_resolve_brand_context_valid_key_returns_brand_context() -> None:
    presented = "riddell_prod_testkey123"
    record = _make_record(presented_key=presented)

    with patch("brand_server.auth.lookup_brand_key", new_callable=AsyncMock) as mock_lookup:
        mock_lookup.return_value = record
        ctx = await resolve_brand_context(presented)

    assert ctx.brand_id == "riddell"
    assert ctx.brand_name == "Riddell"


async def test_resolve_brand_context_none_key_raises_invalid_api_key() -> None:
    with pytest.raises(InvalidAPIKeyError):
        await resolve_brand_context(None)


async def test_resolve_brand_context_unknown_prefix_raises_invalid_api_key() -> None:
    with patch("brand_server.auth.lookup_brand_key", new_callable=AsyncMock) as mock_lookup:
        mock_lookup.return_value = None
        with pytest.raises(InvalidAPIKeyError):
            await resolve_brand_context("unknown_prefix_key")


async def test_resolve_brand_context_revoked_key_raises_invalid_api_key() -> None:
    presented = "riddell_prod_testkey123"
    record = _make_record(status="revoked", presented_key=presented)

    with patch("brand_server.auth.lookup_brand_key", new_callable=AsyncMock) as mock_lookup:
        mock_lookup.return_value = record
        with pytest.raises(InvalidAPIKeyError):
            await resolve_brand_context(presented)


async def test_resolve_brand_context_wrong_secret_raises_invalid_api_key() -> None:
    presented = "riddell_prod_testkey123"
    record = _make_record(presented_key="riddell_prod_differentkey")  # hash for different key

    with patch("brand_server.auth.lookup_brand_key", new_callable=AsyncMock) as mock_lookup:
        mock_lookup.return_value = record
        with pytest.raises(InvalidAPIKeyError):
            await resolve_brand_context(presented)
