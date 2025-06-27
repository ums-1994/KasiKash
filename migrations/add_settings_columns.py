import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from support import db_connection

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

if __name__ == "__main__":
    add_settings_columns() 