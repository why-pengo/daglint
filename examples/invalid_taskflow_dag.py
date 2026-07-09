"""Example of a TaskFlow API DAG file with violations daglint should catch."""
from airflow.decorators import dag, task


@dag(schedule='@daily', default_args={'retries': 1})
def InvalidTaskflowDAG():
    """Bad pipeline: PascalCase name, missing catchup/tags/doc_md/max_active_runs,
    default_args without owner/start_date."""

    @task
    def DoThing():
        return 1

    @task(task_id='duplicate_id')
    def first():
        return 1

    @task(task_id='duplicate_id')
    def second():
        return 2

    DoThing()
    second(first())


InvalidTaskflowDAG()
