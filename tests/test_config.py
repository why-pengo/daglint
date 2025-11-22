"""Tests for daglint configuration."""

import tempfile
from pathlib import Path

import pytest

from daglint.config import Config


def test_default_config():
    """Test default configuration."""
    config = Config.default()
    assert config.is_rule_enabled("dag_id_convention")
    assert config.is_rule_enabled("owner_validation")


def test_config_from_file():
    """Test loading configuration from file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(
            """
rules:
  dag_id_convention:
    enabled: true
    pattern: "^test_.*$"
  owner_validation:
    enabled: false
"""
        )
        f.flush()

        config = Config.from_file(f.name)
        assert config.is_rule_enabled("dag_id_convention")
        assert not config.is_rule_enabled("owner_validation")

        rule_config = config.get_rule_config("dag_id_convention")
        assert rule_config["pattern"] == "^test_.*$"

        Path(f.name).unlink()


def test_get_rule_config():
    """Test getting rule configuration."""
    config = Config.default()
    rule_config = config.get_rule_config("dag_id_convention")
    assert "pattern" in rule_config
    assert "enabled" in rule_config


def test_set_active_rules():
    """Test setting active rules."""
    config = Config.default()
    config.set_active_rules(["dag_id_convention", "owner_validation"])

    assert config.is_rule_enabled("dag_id_convention")
    assert config.is_rule_enabled("owner_validation")
    assert not config.is_rule_enabled("task_id_convention")


def test_generate_default_config():
    """Test generating default configuration file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ".daglint.yaml"
        Config.generate_default_config(str(config_path))

        assert config_path.exists()
        config = Config.from_file(str(config_path))
        assert config.is_rule_enabled("dag_id_convention")
