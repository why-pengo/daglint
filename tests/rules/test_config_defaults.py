"""Tests that the default config is the single source of truth for rule defaults (#50)."""

import ast
from typing import List

import pytest

from daglint.config import Config
from daglint.models import LintIssue
from daglint.rules import AVAILABLE_RULES
from daglint.rules.base import BaseRule


@pytest.mark.parametrize("rule_id", sorted(AVAILABLE_RULES))
def test_unconfigured_rule_inherits_default_config(rule_id):
    """A rule instantiated without config carries its full default config entry."""
    rule = AVAILABLE_RULES[rule_id]()
    for key, value in Config.default_rule_config(rule_id).items():
        assert rule.config[key] == value


@pytest.mark.parametrize("rule_id", sorted(AVAILABLE_RULES))
def test_partial_config_inherits_default_severity(rule_id):
    """A config that omits severity gets the documented default, not a hardcoded one."""
    rule = AVAILABLE_RULES[rule_id]({"enabled": True})
    assert rule.severity == Config.default_rule_config(rule_id)["severity"]


def test_explicit_config_overrides_defaults():
    """Explicitly configured values win over the default config."""
    rule = AVAILABLE_RULES["schedule_validation"]({"severity": "error", "allow_none": True})
    assert rule.severity == "error"
    assert rule.config["allow_none"] is True


def test_rule_without_default_config_entry_falls_back_to_error_severity():
    """Rules unknown to the default config (e.g. third-party) default to error severity."""

    class CustomRule(BaseRule):
        @property
        def rule_id(self) -> str:
            return "custom_rule_not_in_default_config"

        @property
        def description(self) -> str:
            return "Custom rule"

        def check(self, tree: ast.AST, file_path: str, source_code: str) -> List[LintIssue]:
            return []

    rule = CustomRule()
    assert rule.severity == "error"
