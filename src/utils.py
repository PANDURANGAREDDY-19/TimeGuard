import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from sklearn.model_selection import GridSearchCV

from src.exception import CustomException
from src.logger import logging

def save_object(file_path, obj):
    """
    Save a Python object to a file using pickle
    
    Args:
        file_path: Path to save the object
        obj: Python object to save
    """
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        
        with open(file_path, "wb") as file_obj:
            pickle.dump(obj, file_obj)
            
    except Exception as e:
        logging.error(f"Error in save_object: {e}")
        raise CustomException(e, sys)

def load_object(file_path):
    """
    Load a Python object from a file using pickle
    
    Args:
        file_path: Path to the saved object
    """
    try:
        with open(file_path, "rb") as file_obj:
            return pickle.load(file_obj)
            
    except Exception as e:
        logging.error(f"Error in load_object: {e}")
        raise CustomException(e, sys)

def evaluate_models(X_train, y_train, X_test, y_test, models, params):
    """
    Evaluate multiple models with hyperparameter tuning
    
    Args:
        X_train: Training features
        y_train: Training target
        X_test: Test features
        y_test: Test target
        models: Dictionary of models to evaluate
        params: Dictionary of hyperparameters for each model
    """
    try:
        report = {}
        
        for model_name, model in models.items():
            # Get parameters for the current model
            model_params = params[model_name]
            
            # If parameters exist, perform grid search
            if model_params:
                gs = GridSearchCV(model, model_params, cv=3, n_jobs=-1)
                gs.fit(X_train, y_train)
                
                # Set best parameters
                model.set_params(**gs.best_params_)
            
            # Train the model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)
            
            # Calculate R² scores
            train_score = r2_score(y_train, y_train_pred)
            test_score = r2_score(y_test, y_test_pred)
            
            # Store test score in report
            report[model_name] = test_score
            
            logging.info(f"{model_name} - Train Score: {train_score}, Test Score: {test_score}")
        
        return report
        
    except Exception as e:
        logging.error(f"Error in evaluate_models: {e}")
        raise CustomException(e, sys)

def calculate_deviation(estimated_time, actual_time):
    """
    Calculate deviation between estimated and actual time
    
    Args:
        estimated_time: Estimated time in minutes
        actual_time: Actual time in minutes
    """
    return actual_time - estimated_time

def should_send_alert(deviation, threshold=15):
    """
    Determine if an alert should be sent based on deviation
    
    Args:
        deviation: Time deviation in minutes
        threshold: Alert threshold in minutes
    """
    return abs(deviation) > threshold