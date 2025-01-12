import psycopg
import hashlib
import random

DB_CONFIG = {
    "dbname": "stockease_db",
    "user": "postgres",
    "password": "2004",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    return psycopg.connect(**DB_CONFIG)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()

   
    cursor.execute("SELECT id, role, two_factor_enabled FROM users WHERE email = %s AND password = %s", 
                   (email, hash_password(password)))
    user = cursor.fetchone()

    conn.close()
    
    if user:
        user_id, role, two_factor_enabled = user
        return {"id": user_id, "role": role, "two_factor_enabled": two_factor_enabled}, two_factor_enabled
    return None, False

def register_user(email, password, mobile, role="admin", two_factor_enabled=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (email,))
    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO users (username, password_hash, mobile, role, two_factor_enabled) VALUES (%s, %s, %s, %s, %s)",
        (email, hash_password(password), mobile, role, two_factor_enabled)
    )

    conn.commit()
    conn.close()
    return True



otp_storage = {2004}  

def send_otp(email):
    otp = random.randint(100000, 999999)
    otp_storage[email] = otp
    print(f"OTP for {email}: {otp}")  
    return otp

def verify_otp(email, user_otp):
    """Verifies if the entered OTP matches the stored OTP"""
    if email in otp_storage and otp_storage[email] == int(user_otp):
        del otp_storage[email] 
        return True
    return False
