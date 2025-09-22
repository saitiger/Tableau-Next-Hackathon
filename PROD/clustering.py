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

# Setup logging
log_file = "logs/clustering.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Environment variables setup
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")  
CHANNELS = os.getenv("SLACK_CHANNELS", "").split(",") 
DATABASE_URL = os.getenv("DATABASE_URL")  

if not SLACK_TOKEN:
    logging.error("SLACK_BOT_TOKEN environment variable is required")
    raise ValueError("SLACK_BOT_TOKEN environment variable is required")

if not CHANNELS or CHANNELS == ['']:
    logging.error("SLACK_CHANNELS environment variable is required")
    raise ValueError("SLACK_CHANNELS environment variable is required")

client = WebClient(token=SLACK_TOKEN)

def fetch_slack_data():
    """Fetch messages from specified Slack channels"""
    logging.info("Fetching Slack data from channels...")
    all_messages = []
    
    for channel in CHANNELS:
        channel = channel.strip() 
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
    """Preprocess the data for clustering"""
    logging.info("Preprocessing data...")
    
   
    features = ['word_count', 'reaction_count', 'thread_replies']
    df_selected = df[features].fillna(0)
  
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df_selected)
    
    logging.info("Preprocessing complete.")
    return scaled_features, df

def run_kmeans(scaled_features, n_clusters=5):
    """Run KMeans clustering on the scaled features"""
    logging.info(f"Running KMeans with {n_clusters} clusters...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    logging.info("KMeans clustering complete.")
    return clusters

def save_results(df, clusters):
    """Save clustering results to CSV and database"""
    df['cluster'] = clusters

    os.makedirs("data", exist_ok=True)
    output_csv = "data/slack_clusters.csv"
    df.to_csv(output_csv, index=False)
    logging.info(f"Clusters saved to CSV at {output_csv}")
  
    if DATABASE_URL:
        try:
            engine = create_engine(DATABASE_URL)
            df.to_sql('slack_clusters', engine, if_exists='replace', index=False)
            logging.info("Clusters saved to database successfully.")
        except Exception as e:
            logging.error(f"Failed to save to database: {e}")
    else:
        logging.info("DATABASE_URL not provided, skipping database save.")

def main():
    """Main pipeline execution"""
    logging.info("Starting Slack clustering pipeline...")
    
    try:
        df = fetch_slack_data()
        
        if df.empty:
            logging.warning("No data fetched from Slack. Exiting pipeline.")
            return
        
        scaled_features, df_orig = preprocess_data(df)
        clusters = run_kmeans(scaled_features)
        save_results(df_orig, clusters)
        logging.info("Slack clustering pipeline finished successfully.")
        
    except Exception as e:
        logging.error(f"Pipeline failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
