import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in the .env file")

def test_connection():
    print(f"Attempting to connect to: {DATABASE_URL}")
    try:
        result = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=result.hostname,
            port=result.port,
            user=result.username,
            password=result.password,
            dbname=result.path[1:],
            client_encoding='UTF8'
        )
        print("Successfully connected to the database!")
        conn.close()
    except Exception as e:
        print(f"Failed to connect to the database: {e}")

if __name__ == '__main__':
    test_connection()
