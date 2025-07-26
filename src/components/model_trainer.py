import os
import sys
import numpy as np
import pandas as pd
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from pathlib import Path

from src.logger import logging
from src.exception import CustomException
from src.utils import save_object, evaluate_models

@dataclass
class ModelTrainerConfig:
    models_dir: str = os.path.join('artifacts', 'models')
    general_model_path: str = os.path.join('artifacts', 'models', 'general_model.pkl')
    
    def get_user_model_path(self, user_id):
        """Get the file path for a user-specific model"""
        return os.path.join(self.models_dir, f'user_{user_id}_model.pkl')

class ModelTrainer:
    def __init__(self):
        self.model_trainer_config = ModelTrainerConfig()
        # Create models directory if it doesn't exist
        os.makedirs(self.model_trainer_config.models_dir, exist_ok=True)
    
    def initiate_model_trainer(self, train_array, test_array, user_id=None):
        """Train a model based on the provided data
        
        Args:
            train_array: Training data
            test_array: Test data
            user_id: Optional user ID for user-specific model training
        """
        try:
            logging.info("Model training started")
            
            # Split train and test data
            X_train, y_train = train_array[:, :-1], train_array[:, -1]
            X_test, y_test = test_array[:, :-1], test_array[:, -1]
            
            # Define models to train
            models = {
                "Linear Regression": LinearRegression(),
                "Random Forest": RandomForestRegressor(),
                "Gradient Boosting": GradientBoostingRegressor(),
                "XGBoost": XGBRegressor()
            }
            
            # Define hyperparameters for tuning
            params = {
                "Linear Regression": {},
                "Random Forest": {
                    'n_estimators': [50, 100],
                    'max_depth': [10, 20],
                    'min_samples_split': [2, 5]
                },
                "Gradient Boosting": {
                    'n_estimators': [50, 100],
                    'learning_rate': [0.01, 0.1],
                    'max_depth': [3, 5]
                },
                "XGBoost": {
                    'n_estimators': [50, 100],
                    'learning_rate': [0.01, 0.1],
                    'max_depth': [3, 5]
                }
            }
            
            # Evaluate models
            model_report = evaluate_models(
                X_train=X_train, 
                y_train=y_train, 
                X_test=X_test, 
                y_test=y_test, 
                models=models,
                params=params
            )
            
            # Get best model score and name
            best_model_score = max(sorted(model_report.values()))
            best_model_name = list(model_report.keys())[
                list(model_report.values()).index(best_model_score)
            ]
            best_model = models[best_model_name]
            
            logging.info(f"Best model: {best_model_name} with R² score: {best_model_score}")
            
            if best_model_score < 0.3:
                logging.info("No model with good accuracy found")
                raise CustomException("No model with good accuracy found", sys)
            
            # Determine the model file path based on whether it's user-specific or general
            if user_id:
                model_file_path = self.model_trainer_config.get_user_model_path(user_id)
                logging.info(f"Training user-specific model for user {user_id}")
            else:
                model_file_path = self.model_trainer_config.general_model_path
                logging.info("Training general model for all users")
                
            # Save the best model
            save_object(
                file_path=model_file_path,
                obj=best_model
            )
            
            # Make predictions and calculate metrics
            y_pred = best_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            logging.info(f"Model evaluation metrics - MAE: {mae}, RMSE: {rmse}, R²: {r2}")
            logging.info("Model training completed")
            
            return (
                best_model_name,
                best_model_score,
                model_file_path
            )
            
        except Exception as e:
            logging.error(f"Error in model training: {e}")
            raise CustomException(e, sys)
    
    def get_model_for_prediction(self, user_id):
        """
        Get the appropriate model for prediction based on user ID
        
        Args:
            user_id: User identifier
            
        Returns:
            Loaded model object for prediction
        """
        try:
            # Check if user-specific model exists
            user_model_path = self.model_trainer_config.get_user_model_path(user_id)
            if os.path.exists(user_model_path):
                logging.info(f"Using user-specific model for user {user_id}")
                return self.load_model(user_model_path)
            else:
                logging.info(f"No user-specific model found for user {user_id}. Using general model.")
                return self.load_model(self.model_trainer_config.general_model_path)
        except Exception as e:
            logging.error(f"Error loading model for user {user_id}: {e}")
            raise CustomException(e, sys)
    
    def load_model(self, model_path):
        """
        Load a model from the specified path
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Loaded model object
        """
        try:
            import pickle
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logging.error(f"Error loading model from {model_path}: {e}")
            raise CustomException(e, sys)
    
    def train_user_model(self, user_id, user_task_history):
        """
        Train a model specifically for a user based on their task history
        
        Args:
            user_id: User identifier
            user_task_history: DataFrame containing user's task history
            
        Returns:
            Tuple containing model name, score, and file path if successful, None otherwise
        """
        try:
            logging.info(f"Training user-specific model for user {user_id}")
            
            if len(user_task_history) < 5:
                logging.info(f"Not enough task history for user {user_id}. Using general model.")
                return None
            
            # Prepare data for training
            # Assuming user_task_history has columns like:
            # task_type, difficulty_level, estimated_time_minutes, focus_score, time_of_day, day_of_week, actual_minutes
            
            # Feature engineering specific to this user
            features = user_task_history.drop(['actual_minutes'], axis=1)
            target = user_task_history['actual_minutes']
            
            # Convert categorical features to numeric
            features_encoded = pd.get_dummies(features, drop_first=True)
            
            # Split data into train and test sets (80/20)
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                features_encoded, target, test_size=0.2, random_state=42
            )
            
            # Train the model using the existing method
            train_array = np.column_stack((X_train, y_train))
            test_array = np.column_stack((X_test, y_test))
            
            return self.initiate_model_trainer(train_array, test_array, user_id)
            
        except Exception as e:
            logging.error(f"Error in user model training for user {user_id}: {e}")
            raise CustomException(e, sys)
    
    def update_user_model(self, user_id, new_task_data):
        """
        Update a user's model with new task data
        
        Args:
            user_id: User identifier
            new_task_data: DataFrame containing new task data for the user
            
        Returns:
            True if model was updated successfully, False otherwise
        """
        try:
            # Create user data directory if it doesn't exist
            user_data_dir = os.path.join('artifacts', 'user_data')
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Define path for user's task history
            user_history_path = os.path.join(user_data_dir, f'user_{user_id}_history.csv')
            
            # Load existing history or create new if it doesn't exist
            if os.path.exists(user_history_path):
                user_history = pd.read_csv(user_history_path)
                # Append new data
                user_history = pd.concat([user_history, new_task_data], ignore_index=True)
            else:
                user_history = new_task_data
            
            # Save updated history
            user_history.to_csv(user_history_path, index=False)
            
            # Retrain the model if we have enough data
            if len(user_history) >= 5:
                self.train_user_model(user_id, user_history)
                logging.info(f"User model for user {user_id} updated successfully")
                return True
            else:
                logging.info(f"Not enough data to train model for user {user_id} yet")
                return False
                
        except Exception as e:
            logging.error(f"Error updating model for user {user_id}: {e}")
            return False