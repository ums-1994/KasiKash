from support import db_connection
from datetime import datetime, date, timedelta

def award_points(user_id, points):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT points FROM user_points WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                new_points = row[0] + points
                cur.execute("UPDATE user_points SET points = %s WHERE user_id = %s", (new_points, user_id))
            else:
                cur.execute("INSERT INTO user_points (user_id, points) VALUES (%s, %s)", (user_id, points))
            conn.commit()

def award_badge(user_id, badge_name):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM badges WHERE name = %s", (badge_name,))
            badge_row = cur.fetchone()
            if badge_row:
                badge_id = badge_row[0]
                cur.execute("SELECT id FROM user_badges WHERE user_id = %s AND badge_id = %s", (user_id, badge_id))
                if cur.fetchone() is None:
                    cur.execute("INSERT INTO user_badges (user_id, badge_id) VALUES (%s, %s)", (user_id, badge_id))
                    conn.commit()
                    return True
    return False

def update_streak(user_id):
    today = date.today()
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_streak, last_contribution_date FROM streaks WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                current_streak, last_date = row
                if last_date == today:
                    return current_streak
                elif last_date == today - timedelta(days=1):
                    current_streak += 1
                else:
                    current_streak = 1
                cur.execute("UPDATE streaks SET current_streak = %s, last_contribution_date = %s WHERE user_id = %s",
                            (current_streak, today, user_id))
            else:
                current_streak = 1
                cur.execute("INSERT INTO streaks (user_id, current_streak, last_contribution_date) VALUES (%s, %s, %s)",
                            (user_id, current_streak, today))
            conn.commit()
            return current_streak 