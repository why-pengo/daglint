"""Example of a valid DAG file that passes all daglint checks."""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def print_hello():
    """Print hello message."""
    print("Hello from DAGLint!")
    return "Hello"


def print_date():
    """Print current date."""
    print(f"Current date: {datetime.now()}")
    return datetime.now()


with DAG(
    dag_id='example_valid_dag',
    default_args=default_args,
    description='A valid example DAG that passes all daglint checks',
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['environment', 'team', 'example'],
) as dag:

    task_hello = PythonOperator(
        task_id='print_hello',
        python_callable=print_hello,
    )

    task_date = PythonOperator(
        task_id='print_date',
        python_callable=print_date,
    )

    task_bash = BashOperator(
        task_id='print_env',
        bash_command='echo "Environment: production"',
    )

    # Set task dependencies
    task_hello >> [task_date, task_bash]

