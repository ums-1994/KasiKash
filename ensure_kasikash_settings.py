from support import db_connection

KASIKASH_UID = "T8f4wiPKZoTqp8M5QmTwhpAdR142"  # Replace with the correct UID if needed

def ensure_user_settings(user_id):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM user_settings WHERE user_id = %s", (user_id,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO user_settings (
                        user_id,
                        email_notifications,
                        sms_notifications,
                        push_notifications,
                        receive_promotions,
                        receive_updates,
                        weekly_summary,
                        monthly_summary
                    ) VALUES (
                        %s, TRUE, FALSE, TRUE, TRUE, TRUE, FALSE, TRUE
                    )
                """, (user_id,))
                conn.commit()
                print(f"Default settings created for user: {user_id}")
            else:
                print(f"Settings already exist for user: {user_id}")

if __name__ == "__main__":
    ensure_user_settings(KASIKASH_UID) 