import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_SECRET_KEY, Settings

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
