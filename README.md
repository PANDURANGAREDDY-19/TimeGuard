# TimeGuard - ML-Powered Task Time Management

TimeGuard is a web application that uses Machine Learning to estimate task completion times and detect deviations based on user historical data.

## Features

- **User Authentication**: Login/Register system
- **ML Time Estimation**: Predicts task completion time based on historical data
- **Deviation Detection**: Alerts when tasks take significantly longer/shorter than estimated
- **Dual Dashboards**: Separate interfaces for users and administrators
- **Profile Management**: Photo upload and theme switching (light/dark)
- **PostgreSQL Backend**: Robust data storage and management

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Setup**:
   - Install PostgreSQL
   - Create database: `createdb timeguard`
   - Update DATABASE_URL in config.py or .env file

3. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Initialize Database**:
   ```bash
   python init_db.py
   ```

5. **Run Application**:
   ```bash
   python app.py
   ```

## Default Credentials

- **Admin**: admin / admin123
- **Users**: Register new accounts through the web interface

## Usage

### For Users:
- Add new tasks with descriptions and categories
- View ML-generated time estimates
- Complete tasks and track actual time spent
- Receive deviation alerts for time management improvement

### For Administrators:
- View all user activities and statistics
- Access comprehensive analytics and graphs
- Monitor system-wide task completion trends

## ML Features

- **Time Prediction**: Uses Random Forest algorithm trained on historical task data
- **Feature Engineering**: Considers task complexity, user experience, category, and priority
- **Deviation Detection**: Identifies tasks that deviate >30% from estimates
- **Continuous Learning**: Model retrains with new completed task data

## Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, Chart.js, Vanilla JavaScript
- **ML**: scikit-learn, NumPy, Pandas
- **Authentication**: Flask-Login
- **Database Migration**: Flask-Migrate