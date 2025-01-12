import psycopg
from database import DB_CONFIG

def migrate():
    try:
        print("Connecting to database...")
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Dropping incompatible tables if they exist...")
        # Drop tables in correct order to avoid FK constraint errors
        tables_to_drop = [
            'invoices', 'returns', 'sales_orders', 'purchase_orders', 
            'inventory', 'sale_items', 'purchase_items', 
            'sales', 'purchases', 'products', 'categories', 
            'stock_movements', 'suppliers'
        ]
        for table in tables_to_drop:
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        
        print("Creating new tables based on Python code...")

        # 1. Categories
        # Referenced in product.py: SELECT name FROM categories ORDER BY name
        cur.execute("""
            CREATE TABLE categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL
            );
        """)
        
        # 2. Products
        # Referenced in product.py: INSERT INTO products (name, category_id, price)
        cur.execute("""
            CREATE TABLE products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                price NUMERIC(10, 2) NOT NULL
            );
        """)

        # 3. Inventory
        # Referenced in inventory.py: SELECT i.id, c.name AS category, p.name AS product, i.quantity, i.last_order_date
        cur.execute("""
            CREATE TABLE inventory (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE UNIQUE,
                quantity INTEGER DEFAULT 0,
                last_order_date DATE
            );
        """)

        # 4. Sales Orders
        # Referenced in salesorder.py: INSERT INTO sales_orders (product_id, quantity, order_date)
        cur.execute("""
            CREATE TABLE sales_orders (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL,
                order_date DATE DEFAULT CURRENT_DATE
            );
        """)

        # 5. Invoices
        # Referenced in salesorder.py: INSERT INTO invoices (sales_order_id, total_amount)
        cur.execute("""
            CREATE TABLE invoices (
                id SERIAL PRIMARY KEY,
                sales_order_id INTEGER REFERENCES sales_orders(id) ON DELETE CASCADE,
                total_amount NUMERIC(10, 2) NOT NULL
            );
        """)

        # 6. Purchase Orders
        # Referenced in Purchase_Order.py: CREATE TABLE IF NOT EXISTS purchase_orders
        cur.execute("""
            CREATE TABLE purchase_orders (
                id SERIAL PRIMARY KEY,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL,
                order_date DATE NOT NULL,
                executed BOOLEAN DEFAULT FALSE
            );
        """)

        # 7. Returns
        # Referenced in return_refund.py: INSERT INTO returns ...
        cur.execute("""
            CREATE TABLE returns (
                id SERIAL PRIMARY KEY,
                sales_order_id INTEGER REFERENCES sales_orders(id) ON DELETE CASCADE,
                product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                quantity INTEGER NOT NULL,
                return_reason TEXT
            );
        """)
        
        # 8. Users (Keep if exists, or recreate simple one)
        # database.py: INSERT INTO users (username, password_hash, mobile, role, two_factor_enabled)
        # But wait, database.py uses `email` in authenticate_user but `username` in register_user? 
        # Let's check database.py again.
        # authenticate_user: SELECT id, role... FROM users WHERE email = %s AND password = %s
        # BUT query says: SELECT ... WHERE email = %s AND password = %s
        # register_user: INSERT INTO users (username, ...). 
        # authenticate_user uses email, register uses username. This is inconsistent.
        # db_connect.py: INSERT INTO users (email, password).
        # It seems there are two auth systems. Let's create a users table that supports both or minimal.
        
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                username VARCHAR(255) UNIQUE,
                password TEXT, 
                password_hash TEXT,
                mobile VARCHAR(20),
                role VARCHAR(50) DEFAULT 'admin',
                two_factor_enabled BOOLEAN DEFAULT FALSE
            );
        """)
        # Insert default admin user
        # In database.py: user="postgres", password="2004". App might use this for connection, not app login.
        # But app login uses `authenticate_user`.
        # Let's insert a default user if needed.

        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate()
