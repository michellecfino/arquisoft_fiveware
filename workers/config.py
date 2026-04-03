import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            port=os.getenv("DB_PORT", "5432")
        )
        return connection
    except Exception as e:
        print(f"Error conectando a la base de datos: {e}")
        return None