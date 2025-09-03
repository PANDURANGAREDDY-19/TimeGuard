import psycopg2
from config import Config

def add_registration_otp_table():
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
                WHERE table_name = 'registration_otp'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            cursor.execute("""
                CREATE TABLE registration_otp (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(120) NOT NULL,
                    username VARCHAR(80) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE
                )
            """)
            print("Created registration_otp table")
        else:
            print("registration_otp table already exists")
        
        conn.commit()
        print("Registration OTP table migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_registration_otp_table()