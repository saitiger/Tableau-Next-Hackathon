# Slack K-Means Clustering Pipeline

This project automatically fetches Slack messages, performs preprocessing, runs K-Means clustering, and saves the results to CSV and a database. The pipeline is fully automated and scheduled using **Airflow**, with logging, retries, and alerts via email and Slack.  

## Features

- Fetch Slack messages from multiple channels using the Slack API  
- Extract features such as `word_count`, `reaction_count`, and `thread_replies`  
- Preprocess features with scaling for clustering  
- Run **K-Means clustering** on Slack messages  
- Save clustering results to **CSV** and **PostgreSQL database**  
- **Automated monthly execution** with Airflow  
- Logging of all pipeline steps  
- **Email & Slack alerts** on failure  
- Retry mechanism with exponential backoff  

---

## Folder Structure

```

project/
│
├─ dags/
│   └─ clustering\_dag.py        # Airflow DAG
│
├─ data/
│   └─ slack\_messages\_processed.csv  # Optional placeholder CSV
│
├─ logs/
│   └─ clustering.log           # Logs from clustering script
│
├─ clustering.py                # Main clustering pipeline
│
└─ requirements.txt             # Python dependencies

````

---

## Requirements

- Python 3.9+  
- PostgreSQL (optional, for DB save)  
- Airflow 2.x  
- Slack Bot Token with `channels:history` permission  

Install dependencies:

```bash
pip install -r requirements.txt
````

`requirements.txt` includes:

```
pandas
numpy
scikit-learn
SQLAlchemy
psycopg2-binary
slack_sdk
apache-airflow==2.7.1
```

---

## Environment Variables

| Variable              | Description                                                 |
| --------------------- | ----------------------------------------------------------- |
| `SLACK_BOT_TOKEN`     | Slack Bot token with permission to read messages            |
| `SLACK_CHANNELS`      | Comma-separated list of Slack channel IDs to fetch messages |
| `DATABASE_URL`        | PostgreSQL connection string (optional)                     |
| `SLACK_ALERT_CHANNEL` | Slack channel ID for failure alerts                         |
| `ALERT_EMAIL`         | Email address for Airflow failure notifications             |

Example `.env` file:

```
SLACK_BOT_TOKEN=xoxb-1234567890-abcdef
SLACK_CHANNELS=C12345,C67890
DATABASE_URL=postgresql://user:password@localhost:5432/db
SLACK_ALERT_CHANNEL=C98765
ALERT_EMAIL=alerts@example.com
```

---

## Setup

1. Clone the repository:

```bash
git clone <repo_url>
cd project
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables in your `.env` file or system environment.

4. Ensure PostgreSQL is running if saving to DB.

5. Copy `clustering.py` to your Airflow DAG folder if needed (`/usr/local/airflow/dags/`).

---

## Usage

### Run manually

```bash
python clustering.py
```

This will:

* Fetch Slack messages from specified channels
* Preprocess the data
* Run K-Means clustering (default `n_clusters=5`)
* Save results to `data/slack_clusters.csv` and database

### Run via Airflow

* The DAG is scheduled to run **monthly at midnight on the 1st day of the month**.
* Trigger manually via Airflow UI if needed.

---

## Airflow DAG

* DAG name: `slack_kmeans_clustering`
* Location: `dags/clustering_dag.py`
* Features:

  * Retry mechanism (3 retries with exponential backoff)
  * Email notifications on failure
  * Slack alerts on failure

---

## Monitoring & Alerts

* **Logs**: `logs/clustering.log` for pipeline execution
* **Email alerts**: Sent to `ALERT_EMAIL` on failure
* **Slack alerts**: Sent to `SLACK_ALERT_CHANNEL` on failure
