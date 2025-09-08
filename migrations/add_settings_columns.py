import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from support import db_connection
import psycopg2
from support_postgres import db_connection

def add_settings_columns():
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Add notification columns if they don't exist
                cur.execute("""
                    DO $$ 
                    BEGIN 
                        -- Add email_notifications column
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                     WHERE table_name='users' AND column_name='email_notifications') THEN
                            ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT FALSE;
                        END IF;

                        -- Add sms_notifications column
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                     WHERE table_name='users' AND column_name='sms_notifications') THEN
                            ALTER TABLE users ADD COLUMN sms_notifications BOOLEAN DEFAULT FALSE;
                        END IF;

                        -- Add push_notifications column
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                     WHERE table_name='users' AND column_name='push_notifications') THEN
                            ALTER TABLE users ADD COLUMN push_notifications BOOLEAN DEFAULT FALSE;
                        END IF;
                    END $$;
                """)
                conn.commit()
                print("Successfully added settings columns to users table")
    except Exception as e:
        print(f"Error adding settings columns: {str(e)}")
        raise e

def add_admin_settings_columns():
    alter_statements = [
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='admin_settings' AND column_name='enable_dual_approval') THEN
                ALTER TABLE admin_settings ADD COLUMN enable_dual_approval BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='admin_settings' AND column_name='withdrawal_threshold') THEN
                ALTER TABLE admin_settings ADD COLUMN withdrawal_threshold INTEGER DEFAULT 1000;
            END IF;
        END $$;
        """,
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='admin_settings' AND column_name='enable_attendance_tracking') THEN
                ALTER TABLE admin_settings ADD COLUMN enable_attendance_tracking BOOLEAN DEFAULT FALSE;
            END IF;
        END $$;
        """,
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='admin_settings' AND column_name='absence_penalty') THEN
                ALTER TABLE admin_settings ADD COLUMN absence_penalty INTEGER DEFAULT 50;
            END IF;
        END $$;
        """,
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='admin_settings' AND column_name='missed_meetings_threshold') THEN
                ALTER TABLE admin_settings ADD COLUMN missed_meetings_threshold INTEGER DEFAULT 3;
            END IF;
        END $$;
        """
    ]
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                for stmt in alter_statements:
                    cur.execute(stmt)
            conn.commit()
        print("Successfully added new settings columns to admin_settings table.")
    except Exception as e:
        print(f"Error adding settings columns: {str(e)}")

if __name__ == "__main__":
    add_settings_columns()
    add_admin_settings_columns() 