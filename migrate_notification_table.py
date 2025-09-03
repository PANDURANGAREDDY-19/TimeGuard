import psycopg2
from config import Config

def add_notification_table():
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
        
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'admin_notification'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.execute("""
                CREATE TABLE admin_notification (
                    id SERIAL PRIMARY KEY,
                    admin_id INTEGER NOT NULL REFERENCES "user"(id),
                    task_id INTEGER NOT NULL REFERENCES task(id),
                    message VARCHAR(500) NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Created admin_notification table")
        else:
            print("admin_notification table already exists")
        
        conn.commit()
        print("Notification table migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_notification_table()