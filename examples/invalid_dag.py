"""Example of an invalid DAG file with multiple issues."""
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator


# Missing required parameters in default_args
default_args = {
    'owner': 'invalid-team',  # Invalid owner
}


def my_task():
    """Task function."""
    print("Running task")


# Invalid DAG ID (not snake_case)
with DAG(
    dag_id='InvalidDAGID',  # Should be snake_case
    default_args=default_args,
    description='An invalid DAG with multiple issues',
    # Missing schedule_interval
    # Missing catchup
    # Missing tags
) as dag:

    # Invalid task ID (not snake_case)
    Task1 = PythonOperator(
        task_id='InvalidTaskID',  # Should be snake_case
        python_callable=my_task,
    )

    # Duplicate task ID
    Task2 = PythonOperator(
        task_id='InvalidTaskID',  # Duplicate!
        python_callable=my_task,
    )

