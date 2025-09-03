import psycopg2
from config import Config

def add_task_columns():
    # Parse DATABASE_URL
    db_url = Config.SQLALCHEMY_DATABASE_URI
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg2://')
    
    # Extract connection parameters
    import re
    match = re.match(r'postgresql\+psycopg2://([^:]+):([^@]+)@([^/]+)/(.+)', db_url)
    if not match:
        print("Could not parse database URL")
        return
    
    user, password, host_port, database = match.groups()
    host = host_port.split(':')[0]
    port = host_port.split(':')[1] if ':' in host_port else '5432'
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'task' AND column_name IN ('deadline', 'assigned_by')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add deadline column if it doesn't exist
        if 'deadline' not in existing_columns:
            cursor.execute("ALTER TABLE task ADD COLUMN deadline TIMESTAMP")
            print("Added deadline column")
        
        # Add assigned_by column if it doesn't exist
        if 'assigned_by' not in existing_columns:
            cursor.execute("ALTER TABLE task ADD COLUMN assigned_by INTEGER REFERENCES \"user\"(id)")
            print("Added assigned_by column")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_task_columns()