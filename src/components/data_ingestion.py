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
    
    def _create_sample_data(self):
        """
        Create sample data for development purposes
        """
        import numpy as np
        np.random.seed(42)
        
        n_samples = 100
        
        # Sample data with student tasks and time allocations
        data = {
            'student_id': list(range(1, n_samples + 1)),
            'task_type': np.random.choice(['Coding Problem', 'Assignment', 'Reading', 'Project'], n_samples),
            'difficulty_level': np.random.choice([1, 2, 3, 4, 5], n_samples),
            'estimated_time_minutes': np.random.choice([30, 45, 60, 90, 120], n_samples),
            'actual_time_minutes': np.random.choice([35, 50, 70, 100, 130], n_samples),
            'completed_successfully': np.random.choice([True, False], n_samples, p=[0.8, 0.2]),
            'focus_score': np.random.choice([5, 6, 7, 8, 9], n_samples),
            'time_of_day': np.random.choice(['Morning', 'Afternoon', 'Evening', 'Night'], n_samples),
            'day_of_week': np.random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], n_samples),
            'deviation_minutes': np.random.choice([5, 10, -5, -10, 15], n_samples)
        }
        
        return pd.DataFrame(data)