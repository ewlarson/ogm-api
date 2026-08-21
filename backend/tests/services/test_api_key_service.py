"""
Tests for the API key service.
"""

import hashlib
import uuid
from datetime import datetime

import pytest
from sqlalchemy import select

from app.services import api_key_service as api_key_service_module
from app.services.api_key_service import (
    API_KEY_HASH_ITERATIONS,
    APIKeyService,
)
from db.migrations.initialize_api_tiers import initialize_api_tiers
from db.models import api_keys, api_service_tiers
from db.session import async_session


@pytest.mark.unit
class TestAPIKeyService:
    """Test cases for APIKeyService."""

    @pytest.fixture(autouse=True)
    def clear_api_key_cache(self):
        """Keep process-local cache state isolated between tests."""
        APIKeyService.clear_cache()
        yield
        APIKeyService.clear_cache()

    @pytest.fixture
    def api_key_service(self):
        """Create an APIKeyService instance."""
        return APIKeyService()

    def test_generate_api_key(self, api_key_service):
        """Test API key generation."""
        key = api_key_service.generate_api_key()

        # Should be a valid UUID
        uuid.UUID(key)  # Will raise ValueError if not valid UUID
        assert len(key) == 36  # UUID v4 format

    def test_hash_api_key(self, api_key_service, monkeypatch):
        """Test API key hashing."""
        monkeypatch.setenv("API_KEY_HASH_SECRET", "test-hash-secret")
        key = "test-api-key-123"
        key_hash = api_key_service.hash_api_key(key)

        expected_hash = hashlib.pbkdf2_hmac(
            "sha256",
            key.encode("utf-8"),
            b"test-hash-secret",
            API_KEY_HASH_ITERATIONS,
            dklen=32,
        ).hex()

        # Should be a deterministic 64-character hex digest
        assert len(key_hash) == 64
        assert key_hash == expected_hash

    def test_hash_api_key_consistency(self, api_key_service):
        """Test that hashing the same key produces the same hash."""
        key = "test-api-key-123"
        hash1 = api_key_service.hash_api_key(key)
        hash2 = api_key_service.hash_api_key(key)

        assert hash1 == hash2

    def test_hash_api_key_different_keys(self, api_key_service):
        """Test that different keys produce different hashes."""
        key1 = "test-api-key-123"
        key2 = "test-api-key-456"
        hash1 = api_key_service.hash_api_key(key1)
        hash2 = api_key_service.hash_api_key(key2)

        assert hash1 != hash2

    def test_legacy_default_hash_remains_available_for_key_migration(
        self, api_key_service, monkeypatch
    ):
        """The identity rename must not invalidate keys stored with the old fallback salt."""
        monkeypatch.delenv("API_KEY_HASH_SECRET", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)

        key = "pre-ogm-api-key"

        assert api_key_service.hash_api_key(key) != api_key_service.legacy_default_hash_api_key(key)

    @pytest.mark.asyncio
    async def test_validate_api_key_upgrades_legacy_fallback_hash(
        self, api_key_service, monkeypatch
    ):
        """A stored pre-OGM fallback hash is accepted and rewritten in place."""
        monkeypatch.delenv("API_KEY_HASH_SECRET", raising=False)
        monkeypatch.delenv("SECRET_KEY", raising=False)
        initialize_api_tiers()

        key = "pre-ogm-key-to-upgrade"
        old_hash = api_key_service.legacy_default_hash_api_key(key)
        new_hash = api_key_service.hash_api_key(key)
        now = datetime.utcnow()

        async with async_session() as session:
            tier_id = (
                await session.execute(
                    select(api_service_tiers.c.id).where(
                        api_service_tiers.c.tier_name == "anonymous"
                    )
                )
            ).scalar_one()
            key_id = (
                await session.execute(
                    api_keys.insert()
                    .values(
                        key_hash=old_hash,
                        tier_id=tier_id,
                        name="legacy fallback migration test",
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    )
                    .returning(api_keys.c.id)
                )
            ).scalar_one()
            await session.commit()

        tier = await api_key_service.validate_api_key(key)

        assert tier is not None
        assert tier["tier_name"] == "anonymous"
        assert tier["key_hash"] == new_hash

        async with async_session() as session:
            stored_hash = (
                await session.execute(select(api_keys.c.key_hash).where(api_keys.c.id == key_id))
            ).scalar_one()
            await session.execute(api_keys.delete().where(api_keys.c.id == key_id))
            await session.commit()

        assert stored_hash == new_hash

    def test_cache_lookup_key_does_not_store_raw_key(self, api_key_service):
        """Cache keys should not retain the plaintext API key."""
        lookup_key = api_key_service._cache_lookup_key("secret-api-key")

        assert "secret-api-key" not in lookup_key
        assert lookup_key == api_key_service.legacy_hash_api_key("secret-api-key")

    @pytest.mark.asyncio
    async def test_configured_server_api_key_is_unlimited_without_database(
        self, api_key_service, monkeypatch
    ):
        """The deployment frontend key should not depend on destination-local DB rows."""
        monkeypatch.setenv("OPENGEOMETADATA_API_KEY", "frontend-server-key")

        class ExplodingSessionFactory:
            def __call__(self):
                raise AssertionError("configured server key should not query the database")

        monkeypatch.setattr(api_key_service_module, "async_session", ExplodingSessionFactory())

        tier = await api_key_service.validate_api_key(
            "frontend-server-key",
            request_ip="203.0.113.10",
        )

        assert tier is not None
        assert tier["tier_name"] == "ogm_primary"
        assert tier["display_name"] == "OpenGeoMetadata API Frontend"
        assert tier["requests_per_minute"] is None
        assert tier["api_key_id"] is None
        assert tier["key_hash"] == api_key_service.legacy_hash_api_key("frontend-server-key")

    def test_cached_tier_returns_copy_and_expires(self, api_key_service, monkeypatch):
        """Cached tier data should be short-lived and isolated from caller mutation."""
        now = 1000.0
        monkeypatch.setattr(api_key_service_module, "API_KEY_TIER_CACHE_TTL_SECONDS", 60)
        monkeypatch.setattr(api_key_service_module.time, "monotonic", lambda: now)

        api_key_service._set_cached_tier("cache-key", {"tier_id": 1, "tier_name": "ogm"})

        cached_tier = api_key_service._get_cached_tier("cache-key", None)
        cached_tier["tier_id"] = 999

        assert api_key_service._get_cached_tier("cache-key", None)["tier_id"] == 1

        now = 1061.0

        assert api_key_service._get_cached_tier("cache-key", None) is None

    def test_cached_tier_still_enforces_allowed_ips(self, api_key_service, monkeypatch):
        """Cache hits must respect IP allowlists from the cached database row."""
        monkeypatch.setattr(api_key_service_module, "API_KEY_TIER_CACHE_TTL_SECONDS", 60)
        monkeypatch.setattr(api_key_service_module.time, "monotonic", lambda: 1000.0)

        api_key_service._set_cached_tier(
            "cache-key",
            {
                "tier_id": 1,
                "tier_name": "ogm",
                "allowed_ips": ["192.0.2.10"],
            },
        )

        assert api_key_service._get_cached_tier("cache-key", "192.0.2.10") is not None
        assert api_key_service._get_cached_tier("cache-key", "198.51.100.10") is None

    def test_cached_anonymous_tier_returns_copy(self, api_key_service, monkeypatch):
        """Anonymous tier lookups should be cached without exposing shared state."""
        now = 2000.0
        monkeypatch.setattr(api_key_service_module, "API_KEY_TIER_CACHE_TTL_SECONDS", 60)
        monkeypatch.setattr(api_key_service_module.time, "monotonic", lambda: now)

        api_key_service._set_cached_anonymous_tier(
            {
                "tier_id": 6,
                "tier_name": "anonymous",
                "display_name": "Anonymous",
                "requests_per_minute": 10,
            }
        )

        cached_tier = api_key_service._get_cached_anonymous_tier()
        cached_tier["requests_per_minute"] = 999

        assert api_key_service._get_cached_anonymous_tier()["requests_per_minute"] == 10

    def test_last_used_update_is_throttled(self, api_key_service, monkeypatch):
        """Repeated keyed requests should not force last_used_at writes every time."""
        now = 3000.0
        monkeypatch.setattr(
            api_key_service_module,
            "API_KEY_LAST_USED_UPDATE_INTERVAL_SECONDS",
            60,
        )
        monkeypatch.setattr(api_key_service_module.time, "monotonic", lambda: now)

        assert api_key_service._last_used_update_due(42) is True

        api_key_service._remember_last_used_update(42)

        assert api_key_service._last_used_update_due(42) is False

        now = 3061.0

        assert api_key_service._last_used_update_due(42) is True
