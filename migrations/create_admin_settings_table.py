import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "kasikash_db"),
        user=os.getenv("DB_USER", "kasikash_user"),
        password=os.getenv("DB_PASSWORD", "yourpassword"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Create the admin_settings table if it doesn't exist
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                id SERIAL PRIMARY KEY,
                contribution_amount INTEGER,
                late_penalty INTEGER,
                grace_period INTEGER,
                max_loan_percent INTEGER,
                interest_rate INTEGER,
                repayment_period INTEGER,
                language VARCHAR(10),
                role_management VARCHAR(50),
                loan_approval_roles TEXT,
                meeting_frequency VARCHAR(20),
                meeting_time VARCHAR(5),
                meeting_reminders BOOLEAN,
                data_retention VARCHAR(10),
                enable_2fa BOOLEAN,
                meeting_day VARCHAR(10)
            )
        ''')
        # Ensure at least one row exists
        cur.execute('SELECT COUNT(*) FROM admin_settings')
        if cur.fetchone()[0] == 0:
            cur.execute('''
                INSERT INTO admin_settings (
                    contribution_amount, late_penalty, grace_period, max_loan_percent, interest_rate, repayment_period, language, role_management, loan_approval_roles, meeting_frequency, meeting_time, meeting_reminders, data_retention, enable_2fa, meeting_day
                ) VALUES (100, 10, 7, 50, 5, 6, 'en', '', '', 'monthly', '14:00', FALSE, '5', FALSE, 'Monday')
            ''')
        conn.commit()
        print("admin_settings table ensured and default row present.")
    except Exception as e:
        print(f"Error creating or populating admin_settings table: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 