"""
Configuration loader for CLQPSO-GLS.

Loads all algorithm parameters from config/default.yaml.
No magic numbers should exist in any other module — everything
is read from this config.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


# Project root is two levels up from this file (backend/config.py → clqpso-gls/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "default.yaml"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML config file.
            Defaults to config/default.yaml in the project root.

    Returns:
        Dictionary of configuration parameters.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Expected at: {config_path.resolve()}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_optimizer_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract optimizer-specific configuration."""
    return config.get("optimizer", {})


def get_fitness_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract fitness function configuration."""
    return config.get("fitness", {})


def get_graph_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract graph/network configuration."""
    return config.get("graph", {})


def get_vrp_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract VRP problem configuration."""
    return config.get("vrp", {})


def get_benchmark_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract benchmark configuration."""
    return config.get("benchmark", {})


def get_api_config(config: dict[str, Any]) -> dict[str, Any]:
    """Extract API server configuration."""
    return config.get("api", {})


# Convenience: load default config on import
_default_config: dict[str, Any] | None = None


def get_default_config() -> dict[str, Any]:
    """Get the default configuration (cached after first load)."""
    global _default_config
    if _default_config is None:
        _default_config = load_config()
    return _default_config
