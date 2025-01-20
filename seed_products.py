import psycopg
from database import DB_CONFIG
import random

def seed_products():
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        print("Seeding products and inventory...")

        # Map categories to some sample products
        products_data = {
            "Whey Protein": [
                ("Gold Standard 100% Whey", 7500.00),
                ("Nitrotech Whey Gold", 6800.00),
                ("Dymatize ISO 100", 8500.00)
            ],
            "Isolate Protein": [
                ("Isopure Low Carb", 9200.00),
                ("MuscleBlaze Biozyme Iso", 4500.00)
            ],
            "Mass Gainer": [
                ("Serious Mass", 4200.00),
                ("MuscleTech Mass Tech", 3800.00)
            ],
            "Creatine": [
                ("ON Micronized Creatine", 1200.00),
                ("MuscleBlaze Creatine Monohydrate", 800.00)
            ],
             "Pre-Workout": [
                ("C4 Original", 2200.00),
                ("Total War", 2800.00)
            ]
        }

        for category_name, items in products_data.items():
            # Get category ID
            cur.execute("SELECT id FROM categories WHERE name = %s", (category_name,))
            res = cur.fetchone()
            if not res:
                print(f"Skipping {category_name} (not found)")
                continue
            category_id = res[0]

            for product_name, price in items:
                # Insert Product
                cur.execute(
                    """
                    INSERT INTO products (name, category_id, price) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT DO NOTHING 
                    RETURNING id;
                    """,
                    (product_name, category_id, price)
                )
                product_res = cur.fetchone()
                
                # If product already existed, fetch its ID
                if not product_res:
                    cur.execute("SELECT id FROM products WHERE name = %s", (product_name,))
                    product_res = cur.fetchone()
                
                if product_res:
                    product_id = product_res[0]
                    # Insert Inventory (Random quantity between 10 and 100)
                    quantity = random.randint(10, 100)
                    cur.execute(
                        """
                        INSERT INTO inventory (product_id, quantity, last_order_date)
                        VALUES (%s, %s, CURRENT_DATE)
                        ON CONFLICT (product_id) DO UPDATE SET quantity = EXCLUDED.quantity;
                        """,
                        (product_id, quantity)
                    )
                    print(f"Added/Updated: {product_name} (Qty: {quantity})")

        conn.commit()
        print("Products and inventory seeded successfully!")

    except Exception as e:
        print(f"Seeding failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    seed_products()
