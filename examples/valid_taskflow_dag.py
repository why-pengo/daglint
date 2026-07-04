"""Example of a valid TaskFlow API DAG file that passes all daglint checks."""
from datetime import datetime, timedelta

from airflow.decorators import dag, task

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


@dag(
    dag_id='valid_taskflow_dag',
    default_args=default_args,
    description='A valid TaskFlow DAG example',
    schedule='@daily',
    catchup=False,
    max_active_runs=1,
    tags=['environment', 'team'],
    doc_md="""
    ### Valid TaskFlow DAG

    Demonstrates the TaskFlow API style that daglint validates.
    """,
)
def valid_taskflow_dag():
    """Define the pipeline using TaskFlow tasks."""

    @task
    def extract():
        """Extract sample data."""
        return {'value': 42}

    @task
    def transform(data):
        """Transform the extracted data."""
        return {'value': data['value'] * 2}

    @task
    def load(data):
        """Load the transformed data."""
        print(f"Loading: {data}")

    load(transform(extract()))


valid_taskflow_dag()
