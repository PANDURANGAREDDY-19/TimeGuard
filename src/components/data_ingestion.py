import os
import sys
import pandas as pd
from dataclasses import dataclass
from datetime import datetime
from sklearn.model_selection import train_test_split

from src.logger import logging
from src.exception import CustomException

@dataclass
class DataIngestionConfig:
    raw_data_path: str = os.path.join('artifacts', 'raw.csv')
    train_data_path: str = os.path.join('artifacts', 'train.csv')
    test_data_path: str = os.path.join('artifacts', 'test.csv')

class DataIngestion:
    def __init__(self):
        self.ingestion_config = DataIngestionConfig()
        # Create artifacts directory if it doesn't exist
        os.makedirs(os.path.dirname(self.ingestion_config.raw_data_path), exist_ok=True)
    
    def initiate_data_ingestion(self, data_source=None):
        """
        Ingest data from various sources (CSV, database, API)
        
        Args:
            data_source: Path to CSV file or connection string
        """
        try:
            logging.info("Data ingestion started")
            
            # If data source is provided as CSV
            if data_source and data_source.endswith('.csv'):
                df = pd.read_csv(data_source)
            else:
                # Sample data creation for development
                # In production, replace with actual data source
                df = self._create_sample_data()
            
            logging.info(f"Dataset created with shape: {df.shape}")
            
            # Ensure directories exist
            os.makedirs(os.path.dirname(self.ingestion_config.raw_data_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.ingestion_config.train_data_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.ingestion_config.test_data_path), exist_ok=True)
            
            # Save raw data
            df.to_csv(self.ingestion_config.raw_data_path, index=False)
            
            # Split data into train and test sets
            train_set, test_set = train_test_split(df, test_size=0.2, random_state=42)
            
            # Save train and test data
            train_set.to_csv(self.ingestion_config.train_data_path, index=False)
            test_set.to_csv(self.ingestion_config.test_data_path, index=False)
            
            logging.info("Data ingestion completed")
            
            return (
                self.ingestion_config.train_data_path,
                self.ingestion_config.test_data_path
            )
        
        except Exception as e:
            logging.error(f"Error in data ingestion: {e}")
            raise CustomException(e, sys)
    