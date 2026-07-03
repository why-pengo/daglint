"""Tests for daglint configuration."""

import tempfile
from pathlib import Path

import pytest
import yaml

from daglint.config import Config
from daglint.rules import AVAILABLE_RULES

EXAMPLE_CONFIG_PATH = Path(__file__).parent.parent / ".daglint.example.yaml"


def test_default_config():
    """Test default configuration."""
    config = Config.default()
    assert config.is_rule_enabled("dag_id_convention")
    assert config.is_rule_enabled("owner_validation")
    assert config.is_rule_enabled("max_active_runs_validation")


def test_config_from_file():
    """Test loading configuration from file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
rules:
  dag_id_convention:
    enabled: true
    pattern: "^test_.*$"
  owner_validation:
    enabled: false
""")
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

    max_active_runs_config = config.get_rule_config("max_active_runs_validation")
    assert max_active_runs_config["max_active_runs"] == 1


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
        assert config.is_rule_enabled("max_active_runs_validation")
        assert config.get_rule_config("max_active_runs_validation")["max_active_runs"] == 1


def _default_rule_config():
    """Return the rules section of the default config."""
    return Config._default_config()["rules"]


def _example_rule_config():
    """Return the rules section of the committed example config."""
    with open(EXAMPLE_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)["rules"]


def test_default_config_covers_all_rules():
    """Every registered rule has a default config entry, and vice versa."""
    assert set(_default_rule_config()) == set(AVAILABLE_RULES)


def test_example_config_matches_available_rules():
    """The example config's rule set exactly matches AVAILABLE_RULES."""
    assert set(_example_rule_config()) == set(AVAILABLE_RULES)


@pytest.mark.parametrize("rule_id", sorted(AVAILABLE_RULES))
def test_default_rule_entry_has_enabled_and_severity(rule_id):
    """Each default rule entry declares enabled and severity."""
    entry = _default_rule_config()[rule_id]
    assert "enabled" in entry
    assert "severity" in entry
