import psycopg
from database import DB_CONFIG

def seed_categories():
    try:
        conn = psycopg.connect(**DB_CONFIG)
        cur = conn.cursor()

        categories = [
            "Whey Protein",
            "Isolate Protein",
            "Mass Gainer",
            "Creatine",
            "Pre-Workout"
        ]

        print("Seeding categories...")
        for category in categories:
            try:
                cur.execute("INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (category,))
                print(f"Added: {category}")
            except Exception as e:
                print(f"Error adding {category}: {e}")

        conn.commit()
        print("Categories seeded successfully!")

    except Exception as e:
        print(f"Seeding failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    seed_categories()
