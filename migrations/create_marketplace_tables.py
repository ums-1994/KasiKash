import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


def get_conn():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'kasikash_db'),
        user=os.getenv('DB_USER', 'kasikash_user'),
        password=os.getenv('DB_PASSWORD', 'test123'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
    )


def create_tables():
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            # marketplace_items
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_items (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    description TEXT,
                    price_in_points INTEGER NOT NULL,
                    image_url TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            # Optional uniqueness to avoid duplicate seeds by name
            cur.execute(
                """
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM   pg_indexes
                        WHERE  schemaname = 'public'
                        AND    indexname = 'ux_marketplace_items_name'
                    ) THEN
                        CREATE UNIQUE INDEX ux_marketplace_items_name
                        ON marketplace_items (LOWER(name));
                    END IF;
                END $$;
                """
            )

            # marketplace_orders
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS marketplace_orders (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    item_id INTEGER NOT NULL REFERENCES marketplace_items(id) ON DELETE RESTRICT,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    total_points INTEGER NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )

            # donations (used by donate flow)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS donations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    amount INTEGER NOT NULL,
                    cause VARCHAR(128) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
        conn.commit()
        print("✅ marketplace_items, marketplace_orders, and donations tables are ready.")
    finally:
        conn.close()


def seed_items():
    seed = [
        ("Airtime Voucher", "Redeem for mobile airtime.", 15, None, True),
        ("Electricity Voucher", "Prepaid electricity token.", 20, None, True),
        ("Data Bundle", "Mobile data bundle.", 30, None, True),
        ("Movie Ticket", "Enjoy a movie night.", 50, None, True),
        ("Transport Voucher", "Top up your transport card.", 25, None, True),
        ("Clothing Store Voucher", "Shop for apparel.", 60, None, True),
        ("Food Delivery Voucher", "Order your favorite meals.", 40, None, True),
        ("School Supplies Pack", "Stationery essentials.", 35, None, True),
        ("Health & Wellness Voucher", "Health goods/services.", 20, None, True),
    ]

    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            # Insert only missing names (case-insensitive)
            cur.execute("SELECT LOWER(name) FROM marketplace_items")
            existing = {row[0] for row in cur.fetchall()}
            to_insert = [row for row in seed if row[0].lower() not in existing]
            if to_insert:
                execute_values(
                    cur,
                    """
                    INSERT INTO marketplace_items (name, description, price_in_points, image_url, is_active)
                    VALUES %s
                    """,
                    to_insert,
                )
                print(f"✅ Seeded {len(to_insert)} marketplace item(s).")
            else:
                print("ℹ️ Marketplace items already seeded.")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
    seed_items()

