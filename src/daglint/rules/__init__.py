"""Linting rules for DAG files."""

from daglint.rules.base import BaseRule
from daglint.rules.configuration import (
    CatchupValidationRule,
    RetryConfigurationRule,
    ScheduleValidationRule,
)
from daglint.rules.metadata import (
    OwnerValidationRule,
    RequiredDAGParamsRule,
    TagRequirementsRule,
)
from daglint.rules.naming import DAGIDConventionRule, TaskIDConventionRule
from daglint.rules.validation import NoDuplicateTaskIDsRule

# Registry of all available rules
AVAILABLE_RULES = {
    "dag_id_convention": DAGIDConventionRule,
    "owner_validation": OwnerValidationRule,
    "task_id_convention": TaskIDConventionRule,
    "retry_configuration": RetryConfigurationRule,
    "tag_requirements": TagRequirementsRule,
    "no_duplicate_task_ids": NoDuplicateTaskIDsRule,
    "required_dag_params": RequiredDAGParamsRule,
    "catchup_validation": CatchupValidationRule,
    "schedule_validation": ScheduleValidationRule,
}

__all__ = [
    "BaseRule",
    "DAGIDConventionRule",
    "OwnerValidationRule",
    "TaskIDConventionRule",
    "RetryConfigurationRule",
    "TagRequirementsRule",
    "NoDuplicateTaskIDsRule",
    "RequiredDAGParamsRule",
    "CatchupValidationRule",
    "ScheduleValidationRule",
    "AVAILABLE_RULES",
]
