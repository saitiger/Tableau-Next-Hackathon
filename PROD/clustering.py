import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import logging
import os
from sqlalchemy import create_engine
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import datetime

log_file = "logs/clustering.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Slack setup

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")  
CHANNELS = os.getenv("SLACK_CHANNELS", "").split(",")  
client = WebClient(token=SLACK_TOKEN)


# Fetching Slack messages

def fetch_slack_data():
    logging.info("Fetching Slack data from channels...")
    all_messages = []
    
    for channel in CHANNELS:
        try:
            result = client.conversations_history(channel=channel, limit=1000)  
            messages = result['messages']
            
            for msg in messages:
                all_messages.append({
                    'channel': channel,
                    'user': msg.get('user', ''),
                    'text': msg.get('text', ''),
                    'ts': msg.get('ts', ''),
                    'thread_replies': msg.get('reply_count', 0) if 'reply_count' in msg else 0,
                    'reaction_count': sum([r['count'] for r in msg.get('reactions', [])]) if 'reactions' in msg else 0,
                    'word_count': len(msg.get('text', '').split())
                })
            
            logging.info(f"Fetched {len(messages)} messages from channel {channel}")
        
        except SlackApiError as e:
            logging.error(f"Error fetching messages from channel {channel}: {e.response['error']}")

    df = pd.DataFrame(all_messages)
    logging.info(f"Total messages fetched: {len(df)}")
    return df

def preprocess_data(df):
    logging.info("Preprocessing data...")
    
    features = ['word_count', 'reaction_count', 'thread_replies']
    df_selected = df[features].fillna(0)
    
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_selected)
    
    logging.info("Preprocessing complete.")
    return scaled_features, df

def run_kmeans(scaled_features, n_clusters=5):
    logging.info(f"Running KMeans with {n_clusters} clusters...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    logging.info("KMeans clustering complete.")
    return clusters

def save_results(df, clusters):
    df['cluster'] = clusters
    os.makedirs("data", exist_ok=True)
    output_csv = "data/slack_clusters.csv"
    df.to_csv(output_csv, index=False)
    logging.info(f"Clusters saved to CSV at {output_csv}")
    
    try:
        engine = create_engine(os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/db"))
        df.to_sql('slack_clusters', engine, if_exists='replace', index=False)
        logging.info("Clusters saved to database successfully.")
    except Exception as e:
        logging.error(f"Failed to save to database: {e}")

def main():
    logging.info("Starting Slack clustering pipeline...")
    df = fetch_slack_data()
    
    if df.empty:
        logging.warning("No data fetched from Slack. Exiting pipeline.")
        return
    
    scaled_features, df_orig = preprocess_data(df)
    clusters = run_kmeans(scaled_features)
    save_results(df_orig, clusters)
    logging.info("Slack clustering pipeline finished successfully.")

if __name__ == "__main__":
    main()
