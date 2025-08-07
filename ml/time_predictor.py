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
    
    def _extract_keywords(self, text, top_n=3):
        # Simple keyword extraction: most frequent words (excluding stopwords)
        import re
        from collections import Counter
        stopwords = set(['the','and','to','of','in','for','on','at','a','an','is','with','by','as','it','from','this','that','be','are','was','were','or','but','not','your','you'])
        words = re.findall(r'\w+', (text or '').lower())
        words = [w for w in words if w not in stopwords and len(w) > 2]
        most_common = [w for w, _ in Counter(words).most_common(top_n)]
        return most_common

    def _encode_keywords(self, keywords):
        # Hash keywords to a fixed-length vector (simple bag-of-words)
        vec = [0, 0, 0]
        for i, kw in enumerate(keywords[:3]):
            vec[i] = hash(kw) % 1000 / 1000  # normalize to [0,1]
        return vec

    def _user_stats(self, user):
        # Returns (avg_time, std_time, completed_count)
        completed = [t.actual_time for t in user.tasks if t.actual_time]
        if completed:
            avg = float(np.mean(completed))
            std = float(np.std(completed))
            count = len(completed)
        else:
            avg, std, count = 1.0, 0.0, 0
        return avg, std, count

    def prepare_features(self, tasks):
        features = []
        for task in tasks:
            if task.actual_time:
                # NLP features from description
                keywords = self._extract_keywords(task.description)
                keyword_vec = self._encode_keywords(keywords)
                # User stats
                avg_time, std_time, completed_count = self._user_stats(task.user)
                feature = [
                    len(task.title),
                    len(task.description or ''),
                    self._encode_category(task.category or 'general'),
                    self._encode_priority(task.priority),
                    avg_time,
                    std_time,
                    completed_count,
                    *keyword_vec
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
        # NLP features from description
        keywords = self._extract_keywords(task_data.get('description', ''))
        keyword_vec = self._encode_keywords(keywords)
        # User stats
        avg_time, std_time, completed_count = self._user_stats(user)
        feature = np.array([[
            len(task_data.get('title', '')),
            len(task_data.get('description', '')),
            self._encode_category(task_data.get('category', 'general')),
            self._encode_priority(task_data.get('priority', 'medium')),
            avg_time,
            std_time,
            completed_count,
            *keyword_vec
        ]])
        try:
            prediction = self.model.predict(feature)[0]
            return max(0.1, prediction)  # Minimum 6 minutes
        except Exception as e:
            # Fallback: use category average for this user
            print('Warning: ML model not fitted, using category average. Details:', e)
            category = task_data.get('category', 'general')
            cat_times = [t.actual_time for t in user.tasks if t.category == category and t.actual_time]
            if cat_times:
                return float(np.mean(cat_times))
            # Fallback: use user average
            completed = [t.actual_time for t in user.tasks if t.actual_time]
            if completed:
                return float(np.mean(completed))
            # Fallback: global average (could be improved)
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