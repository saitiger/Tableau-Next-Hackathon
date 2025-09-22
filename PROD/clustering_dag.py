from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.email import send_email
from datetime import datetime, timedelta
import subprocess
import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Logging setup

log_file = "/usr/local/airflow/logs/clustering_dag.log"
os.makedirs(os.path.dirname(log_file), exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)


SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
ALERT_CHANNEL = os.getenv("SLACK_ALERT_CHANNEL", "")  # Channel ID for alerts
client = WebClient(token=SLACK_TOKEN)

def send_slack_alert(message):
    if SLACK_TOKEN and ALERT_CHANNEL:
        try:
            client.chat_postMessage(channel=ALERT_CHANNEL, text=message)
            logging.info(f"Slack alert sent: {message}")
        except SlackApiError as e:
            logging.error(f"Failed to send Slack alert: {e.response['error']}")
    else:
        logging.warning("Slack alert not sent: Missing token or channel")


def run_clustering():
    logging.info("Triggering clustering script from Airflow DAG...")
    try:
        result = subprocess.run(
            ["python3", "/usr/local/airflow/dags/clustering.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Clustering script failed: {e.stderr}")
        send_email(
            to=["alerts@example.com"],  # Your email list
            subject="Slack Clustering DAG Failed",
            html_content=f"<pre>{e.stderr}</pre>"
        )
        send_slack_alert(f":x: Slack Clustering DAG failed!\nError:\n{e.stderr}")
        raise


# DAG definition

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['alerts@example.com'], 
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30)
}

dag = DAG(
    'slack_kmeans_clustering',
    default_args=default_args,
    description='Monthly clustering of Slack messages using KMeans with alerts',
    schedule_interval='0 0 1 * *',  # First day of every month at midnight
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1
)

run_clustering_task = PythonOperator(
    task_id='run_clustering',
    python_callable=run_clustering,
    dag=dag
)

run_clustering_task
