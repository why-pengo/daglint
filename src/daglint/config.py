"""Configuration management for daglint."""

from typing import Any, Dict, List, Optional

import yaml


class Config:
    """Configuration for DAGLint."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration.

        Args:
            config_dict: Configuration dictionary
        """
        self.config = config_dict or self._default_config()
        self.rules_config = self.config.get("rules", {})

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
                "catchup_validation": {
                    "enabled": True,
                    "default_catchup": False,
                    "severity": "warning",
                },
            }
        }

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
        return self.rules_config.get(rule_id, {})

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled.

        Args:
            rule_id: Rule identifier

        Returns:
            True if rule is enabled
        """
        rule_config = self.get_rule_config(rule_id)
        return rule_config.get("enabled", True)

    def set_active_rules(self, rule_ids: List[str]) -> None:
        """Enable only specified rules.

        Args:
            rule_ids: List of rule IDs to enable
        """
        for rule_id in self.rules_config:
            self.rules_config[rule_id]["enabled"] = rule_id in rule_ids

    @staticmethod
    def generate_default_config(output_path: str) -> None:
        """Generate a default configuration file.

        Args:
            output_path: Path to write configuration file
        """
        config = Config._default_config()
        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
