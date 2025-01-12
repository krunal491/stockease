import psycopg
from database import DB_CONFIG




def get_db_connection():
    """Establish a PostgreSQL connection."""
    return psycopg.connect(**DB_CONFIG)


def authenticate_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone() 
    
    cursor.close()
    conn.close()
    
    return user is not None  


def register_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        conn.commit()
        success = True  
    except psycopg.IntegrityError:
        conn.rollback()  
        success = False  
    
    cursor.close()
    conn.close()
    
    return success
