import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from models.task import Task
from models.user import User
import pickle
import os

class TimePredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.label_encoders = {}
        self.is_trained = False
        self.model_path = None  # Set per user

    def _get_model_path(self, user_id):
        return f'ml/time_model_{user_id}.pkl'
    
    def prepare_features(self, tasks):
        features = []
        for task in tasks:
            if task.actual_time:
                feature = [
                    len(task.title),
                    len(task.description or ''),
                    self._encode_category(task.category or 'general'),
                    self._encode_priority(task.priority),
                    len(task.user.tasks)  # user experience factor
                ]
                features.append(feature)
        return np.array(features)
    
    def _encode_category(self, category):
        if 'category' not in self.label_encoders:
            self.label_encoders['category'] = LabelEncoder()
        
        try:
            return self.label_encoders['category'].transform([category])[0]
        except:
            # Handle unseen categories
            return 0
    
    def _encode_priority(self, priority):
        priority_map = {'low': 1, 'medium': 2, 'high': 3}
        return priority_map.get(priority, 2)
    
    def train(self, user_id=None):
        if not user_id:
            raise ValueError('user_id is required for per-user model training')
        self.model_path = self._get_model_path(user_id)
        query = Task.query.filter(Task.actual_time.isnot(None), Task.user_id == user_id)
        tasks = query.all()
        if len(tasks) < 5:  # Need minimum data
            return False
        # Fit label encoders first
        categories = [task.category or 'general' for task in tasks]
        if 'category' not in self.label_encoders:
            self.label_encoders['category'] = LabelEncoder()
        self.label_encoders['category'].fit(categories)
        X = self.prepare_features(tasks)
        y = np.array([task.actual_time for task in tasks])
        self.model.fit(X, y)
        self.is_trained = True
        self._save_model()
        return True
    
    def predict(self, task_data, user):
        self.model_path = self._get_model_path(user.id)
        if not self.is_trained:
            self._load_model()
        feature = np.array([[
            len(task_data.get('title', '')),
            len(task_data.get('description', '')),
            self._encode_category(task_data.get('category', 'general')),
            self._encode_priority(task_data.get('priority', 'medium')),
            len(user.tasks)
        ]])
        try:
            prediction = self.model.predict(feature)[0]
            return max(0.1, prediction)  # Minimum 6 minutes
        except Exception as e:
            print('Warning: ML model not fitted, returning default estimate. Details:', e)
            return 1.0
    
    def detect_deviation(self, task):
        if not task.estimated_time or not task.actual_time:
            return False, 0
        
        deviation = (task.actual_time - task.estimated_time) / task.estimated_time
        is_significant = abs(deviation) > 0.3  # 30% threshold
        return is_significant, deviation
    
    def _save_model(self):
        if not self.model_path:
            raise ValueError('model_path must be set before saving model')
        model_data = {
            'model': self.model,
            'label_encoders': self.label_encoders,
            'is_trained': self.is_trained
        }
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)

    def _load_model(self):
        if not self.model_path:
            raise ValueError('model_path must be set before loading model')
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.label_encoders = model_data['label_encoders']
                self.is_trained = model_data['is_trained']