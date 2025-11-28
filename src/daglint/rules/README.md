# DAGLint Rules Module

This module contains all linting rules organized by category.

## Module Structure

```
rules/
├── __init__.py           # Exports all rules and AVAILABLE_RULES registry
├── base.py              # BaseRule abstract class
├── naming.py            # Naming convention rules (DAG IDs, Task IDs)
├── configuration.py     # DAG configuration rules (retries, catchup, schedule)
├── metadata.py          # Metadata validation rules (owner, tags, params)
└── validation.py        # DAG structure validation rules (duplicates, etc.)
```

## Adding New Rules

To add a new rule:

1. Choose the appropriate module based on the rule category:
   - **naming.py**: Rules for naming conventions
   - **configuration.py**: Rules for DAG/task configuration parameters
   - **metadata.py**: Rules for metadata and documentation
   - **validation.py**: Rules for structural validation

2. Create a new class that extends `BaseRule`:
   ```python
   from daglint.rules.base import BaseRule
   
   class MyNewRule(BaseRule):
       @property
       def rule_id(self) -> str:
           return "my_new_rule"
       
       @property
       def description(self) -> str:
           return "Description of what this rule checks"
       
       def check(self, tree, file_path, source_code):
           # Implementation
           pass
   ```

3. Export the rule in `__init__.py`:
   - Add the import
   - Add to `AVAILABLE_RULES` dictionary
   - Add to `__all__` list

4. Write tests in `tests/test_rules.py`

## Rule Categories

### Naming Rules (`naming.py`)
- `DAGIDConventionRule`: Validates DAG ID naming patterns
- `TaskIDConventionRule`: Validates task ID naming patterns

### Configuration Rules (`configuration.py`)
- `RetryConfigurationRule`: Validates retry settings
- `CatchupValidationRule`: Ensures catchup is explicitly set
- `ScheduleValidationRule`: Validates schedule_interval configuration

### Metadata Rules (`metadata.py`)
- `OwnerValidationRule`: Validates DAG owner is set and valid
- `TagRequirementsRule`: Ensures required tags are present
- `RequiredDAGParamsRule`: Validates required DAG parameters

### Validation Rules (`validation.py`)
- `NoDuplicateTaskIDsRule`: Prevents duplicate task IDs within a DAG

