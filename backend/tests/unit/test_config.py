import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_SECRET_KEY, KNOWN_PLACEHOLDER_KEYS, Settings

STRONG_KEY = "x" * 64


class TestSecretKeyGuard:
    def test_development_allows_default_key(self):
        s = Settings(ENVIRONMENT="development", SECRET_KEY=DEFAULT_SECRET_KEY)
        assert s.SECRET_KEY == DEFAULT_SECRET_KEY

    @pytest.mark.parametrize("env", ["staging", "production"])
    def test_non_development_rejects_default_key(self, env):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(ENVIRONMENT=env, SECRET_KEY=DEFAULT_SECRET_KEY)

    @pytest.mark.parametrize("env", ["staging", "production"])
    def test_non_development_rejects_short_key(self, env):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(ENVIRONMENT=env, SECRET_KEY="too-short")

    def test_production_accepts_strong_key(self):
        s = Settings(ENVIRONMENT="production", SECRET_KEY=STRONG_KEY)
        assert s.SECRET_KEY == STRONG_KEY

    def test_unknown_environment_rejected(self):
        with pytest.raises(ValidationError):
            Settings(ENVIRONMENT="prod-typo", SECRET_KEY=STRONG_KEY)


class TestFailClosed:
    def test_environment_defaults_to_production(self, monkeypatch):
        monkeypatch.delenv("SECUREOPS_ENVIRONMENT", raising=False)
        monkeypatch.delenv("SECUREOPS_SECRET_KEY", raising=False)
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(_env_file=None)

    @pytest.mark.parametrize("key", sorted(KNOWN_PLACEHOLDER_KEYS))
    def test_known_placeholders_rejected_in_production(self, key):
        with pytest.raises(ValidationError, match="SECRET_KEY"):
            Settings(ENVIRONMENT="production", SECRET_KEY=key)

    def test_env_example_placeholder_is_denylisted(self):
        from pathlib import Path

        example = Path(__file__).parents[2] / ".env.example"
        for line in example.read_text().splitlines():
            if line.startswith("SECUREOPS_SECRET_KEY="):
                value = line.split("=", 1)[1]
                assert value == "" or value in KNOWN_PLACEHOLDER_KEYS
