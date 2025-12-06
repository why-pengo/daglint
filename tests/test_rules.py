"""Tests for linting rules.

This module re-exports all rule tests from the rules subdirectory
for backward compatibility and easy discovery.
"""

# Import all test classes from the rules subdirectory
from tests.rules.test_catchup_validation import TestCatchupValidationRule
from tests.rules.test_dag_id_convention import TestDAGIDConventionRule
from tests.rules.test_no_duplicate_task_ids import TestNoDuplicateTaskIDsRule
from tests.rules.test_owner_validation import TestOwnerValidationRule
from tests.rules.test_required_dag_params import TestRequiredDAGParamsRule
from tests.rules.test_retry_configuration import TestRetryConfigurationRule
from tests.rules.test_schedule_validation import TestScheduleValidationRule
from tests.rules.test_tag_requirements import TestTagRequirementsRule
from tests.rules.test_task_id_convention import TestTaskIDConventionRule

__all__ = [
    "TestCatchupValidationRule",
    "TestDAGIDConventionRule",
    "TestNoDuplicateTaskIDsRule",
    "TestOwnerValidationRule",
    "TestRequiredDAGParamsRule",
    "TestRetryConfigurationRule",
    "TestScheduleValidationRule",
    "TestTagRequirementsRule",
    "TestTaskIDConventionRule",
]
