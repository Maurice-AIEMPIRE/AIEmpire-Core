"""AIEmpire-Core centralized configuration module."""

from config.env_config import get_api_key, get_config, validate_env

__all__ = ["get_config", "get_api_key", "validate_env"]
