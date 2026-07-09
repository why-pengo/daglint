"""Every DAG-scoped rule must treat all DAG call spellings identically (#33)."""

import ast

import pytest

from daglint.config import Config
from daglint.rules import AVAILABLE_RULES

DAG_SCOPED_RULES = [
    "dag_id_convention",
    "catchup_validation",
    "schedule_validation",
    "tag_requirements",
    "doc_md_validation",
    "max_active_runs_validation",
]

# The same minimal DAG — violating every DAG-scoped rule — spelled five ways.
SPELLINGS = {
    "bare_name": "dag = DAG('InvalidDAGID')\n",
    "attribute": "import airflow\ndag = airflow.DAG('InvalidDAGID')\n",
    "context_manager": "with DAG('InvalidDAGID') as dag:\n    pass\n",
    "taskflow": "from airflow.decorators import dag\n\n@dag('InvalidDAGID')\ndef my_pipeline():\n    pass\n",
    "taskflow_bare": "from airflow.decorators import dag\n\n@dag\ndef InvalidDAGID():\n    pass\n",
}


def _issue_messages(rule_id: str, code: str) -> list:
    rule = AVAILABLE_RULES[rule_id](Config.default().get_rule_config(rule_id))
    tree = ast.parse(code)
    return [issue.message for issue in rule.check(tree, "test.py", code)]


@pytest.mark.parametrize("rule_id", DAG_SCOPED_RULES)
def test_rule_covers_all_dag_call_spellings(rule_id):
    """A violating DAG must produce the same issues regardless of call spelling."""
    results = {spelling: _issue_messages(rule_id, code) for spelling, code in SPELLINGS.items()}

    for spelling, messages in results.items():
        assert messages, f"{rule_id} produced no issues for the {spelling} spelling"

    reference = results["bare_name"]
    for spelling, messages in results.items():
        assert messages == reference, f"{rule_id}: {spelling} spelling diverges from bare_name"
