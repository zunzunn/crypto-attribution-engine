"""Settings tests: defaults, env overrides, derived properties."""

from __future__ import annotations

import pytest

from app.core.config import Settings


class TestSettings:
    def test_defaults(self) -> None:
        s = Settings(_env_file=None)
        assert s.app_name == "crypto-attribution-engine"
        assert s.api_prefix == "/api/v1"
        assert s.database_url.startswith("postgresql+asyncpg")
        assert s.etherscan_api_key == ""
        assert s.etherscan_resolved_base_url == "https://api.etherscan.io/v2/api"

    def test_env_vars_override_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/x")
        monkeypatch.setenv("ETHERSCAN_API_KEY", "k-123")
        s = Settings(_env_file=None)
        assert s.database_url == "postgresql+asyncpg://u:p@localhost:5432/x"
        assert s.etherscan_api_key == "k-123"

    def test_cors_origins_parsed_from_json_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CORS_ORIGINS", '["http://a", "http://b"]')
        s = Settings(_env_file=None)
        assert s.cors_origins == ["http://a", "http://b"]

    def test_etherscan_chain_id_resolution(self) -> None:
        assert Settings(_env_file=None, etherscan_network="mainnet").etherscan_resolved_chain_id == 1
        assert Settings(_env_file=None, etherscan_network="sepolia").etherscan_resolved_chain_id == 11155111
        assert Settings(_env_file=None, etherscan_chain_id=137).etherscan_resolved_chain_id == 137

    def test_unsupported_network_raises(self) -> None:
        s = Settings(_env_file=None, etherscan_network="mars")
        with pytest.raises(ValueError, match="Unsupported ETHERSCAN_NETWORK"):
            _ = s.etherscan_resolved_chain_id

    def test_base_url_override(self) -> None:
        s = Settings(_env_file=None, etherscan_base_url="https://example.test/api/")
        assert s.etherscan_resolved_base_url == "https://example.test/api"