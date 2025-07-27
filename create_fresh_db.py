import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_HOST = 'localhost'
DB_USER = 'postgres'
DB_PASSWORD = 'pandu'
DB_NAME = 'timeguard_fresh'

try:
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database='postgres'  # Connect to default database first
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Drop database if exists and create new one
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    cursor.execute(f"CREATE DATABASE {DB_NAME};")
    
    print(f"Database '{DB_NAME}' created successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("Make sure PostgreSQL is running and credentials are correct")