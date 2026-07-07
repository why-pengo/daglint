"""Configuration management for daglint."""

from typing import Any, Dict, List, Optional

import yaml

VALID_SEVERITIES = ("error", "warning", "info")


class ConfigError(ValueError):
    """Raised when a configuration file contains invalid values."""


class Config:
    """Configuration for DAGLint."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration.

        Args:
            config_dict: Configuration dictionary

        Raises:
            ConfigError: If the configuration contains invalid values
        """
        self.config = config_dict or self._default_config()
        self.rules_config = self.config.get("rules", {})
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values, failing fast with a clear message."""
        excludes = self.config.get("exclude", [])
        if not isinstance(excludes, list) or not all(isinstance(p, str) for p in excludes):
            raise ConfigError("'exclude' must be a list of directory-name patterns")

        for rule_id, rule_config in self.rules_config.items():
            if not isinstance(rule_config, dict):
                continue
            severity = rule_config.get("severity")
            if severity is not None and severity not in VALID_SEVERITIES:
                raise ConfigError(
                    f"Invalid severity '{severity}' for rule '{rule_id}'. "
                    f"Valid severities are: {', '.join(VALID_SEVERITIES)}"
                )

    @property
    def excludes(self) -> List[str]:
        """Directory-name patterns to exclude, on top of the built-in defaults."""
        return list(self.config.get("exclude", []))

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "rules": {
                "dag_id_convention": {
                    "enabled": True,
                    "pattern": r"^[a-z][a-z0-9_]*$",
                    "severity": "error",
                },
                "owner_validation": {
                    "enabled": True,
                    "valid_owners": ["data-team", "analytics-team", "airflow"],
                    "severity": "error",
                },
                "task_id_convention": {
                    "enabled": True,
                    "pattern": r"^[a-z][a-z0-9_]*$",
                    "severity": "error",
                },
                "group_id_convention": {
                    "enabled": True,
                    "pattern": r"^[a-z][a-z0-9_]*$",
                    "severity": "error",
                },
                "retry_configuration": {
                    "enabled": True,
                    "min_retries": 1,
                    "max_retries": 5,
                    "severity": "warning",
                },
                "tag_requirements": {
                    "enabled": True,
                    "required_tags": ["environment", "team"],
                    "severity": "warning",
                },
                "schedule_validation": {
                    "enabled": True,
                    "allow_none": False,
                    "severity": "warning",
                },
                "no_duplicate_task_ids": {
                    "enabled": True,
                    "severity": "error",
                },
                "required_dag_params": {
                    "enabled": True,
                    "required_params": ["owner", "start_date", "retries"],
                    "severity": "error",
                },
                "max_active_runs_validation": {
                    "enabled": True,
                    "max_active_runs": 1,
                    "severity": "warning",
                },
                "catchup_validation": {
                    "enabled": True,
                    "default_catchup": False,
                    "severity": "warning",
                },
                "doc_md_validation": {
                    "enabled": True,
                    "severity": "warning",
                },
            }
        }

    @staticmethod
    def default_rule_config(rule_id: str) -> Dict[str, Any]:
        """Get the default configuration for a single rule.

        Args:
            rule_id: Rule identifier

        Returns:
            The rule's default configuration, or an empty dict for
            rules not in the default config
        """
        return dict(Config._default_config()["rules"].get(rule_id, {}))

    @classmethod
    def default(cls) -> "Config":
        """Create a default configuration."""
        return cls()

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from a YAML file.

        Args:
            path: Path to configuration file

        Returns:
            Config instance
        """
        with open(path, "r") as f:
            config_dict = yaml.safe_load(f)
        return cls(config_dict)

    def get_rule_config(self, rule_id: str) -> Dict[str, Any]:
        """Get configuration for a specific rule.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule configuration dictionary
        """
        return dict(self.rules_config.get(rule_id, {}))

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled.

        Args:
            rule_id: Rule identifier

        Returns:
            True if rule is enabled
        """
        rule_config = self.get_rule_config(rule_id)
        return bool(rule_config.get("enabled", True))

    def set_active_rules(self, rule_ids: List[str], all_rule_ids: Optional[List[str]] = None) -> None:
        """Enable only the specified rules, disabling all others.

        Args:
            rule_ids: List of rule IDs to enable
            all_rule_ids: Full universe of known rule IDs. Rules listed here
                but absent from the loaded config get an explicit disabled
                entry, so a partial config file cannot leave them enabled
                by default.
        """
        universe = set(self.rules_config) | set(rule_ids) | set(all_rule_ids or [])
        for rule_id in universe:
            self.rules_config.setdefault(rule_id, {})["enabled"] = rule_id in rule_ids

    @staticmethod
    def generate_default_config(output_path: str) -> None:
        """Generate a default configuration file.

        Args:
            output_path: Path to write configuration file
        """
        config = Config._default_config()
        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
