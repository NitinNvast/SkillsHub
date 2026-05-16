"""API tests for root / and /health endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestRootEndpoint:
    async def test_root_returns_service_info(self, anon_client):
        response = await anon_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "SkillsHub API"
        assert data["status"] == "ok"
        assert "version" in data

    async def test_root_accessible_without_auth(self, anon_client):
        response = await anon_client.get("/")
        assert response.status_code == 200


class TestHealthEndpoint:
    async def test_health_returns_ok_status(self, anon_client):
        with (
            patch("app.ai.providers.ai_manager") as mock_ai,
        ):
            mock_ai.describe_routes.return_value = {
                "extraction": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
                "embedding": {"provider": "voyage", "model": "voyage-3-large"},
            }
            mock_ai.health = AsyncMock(return_value={"groq": True, "embedding:voyage": True})

            response = await anon_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_health_includes_provider_routes(self, anon_client):
        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.describe_routes.return_value = {
                "extraction": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
                "embedding": {"provider": "voyage", "model": "voyage-3-large"},
            }
            mock_ai.health = AsyncMock(return_value={"groq": True})

            response = await anon_client.get("/health")

        data = response.json()
        assert "providers" in data
        assert "provider_health" in data

    async def test_health_accessible_without_auth(self, anon_client):
        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.describe_routes.return_value = {}
            mock_ai.health = AsyncMock(return_value={})

            response = await anon_client.get("/health")

        assert response.status_code == 200

    async def test_health_provider_health_is_dict(self, anon_client):
        with patch("app.ai.providers.ai_manager") as mock_ai:
            mock_ai.describe_routes.return_value = {}
            mock_ai.health = AsyncMock(return_value={"groq": True, "voyage": False})

            response = await anon_client.get("/health")

        data = response.json()
        assert isinstance(data["provider_health"], dict)
