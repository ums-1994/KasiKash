from support import db_connection


def delete_user_by_email(email):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE email = %s", (email,))
            conn.commit()
            print(f"User with email {email} deleted from local database.")


if __name__ == "__main__":
    # Change the email below if you want to delete a different user
    delete_user_by_email("kasikash34@gmail.com") 