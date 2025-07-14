import psycopg2
import psycopg2.extras
from contextlib import contextmanager
import logging
from config import Config

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections with proper error handling"""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
        conn.autocommit = False
        yield conn
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")

@contextmanager
def get_db_cursor():
    """Context manager for database cursors"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cursor, conn
        finally:
            cursor.close()

def execute_query(operation, query, params=None):
    """
    Execute a database query with proper error handling
    
    Args:
        operation (str): 'search', 'insert', 'update', or 'delete'
        query (str): SQL query string
        params (tuple): Query parameters
        
    Returns:
        Query results or None on error
    """
    try:
        with get_db_cursor() as (cursor, conn):
            logger.debug(f"Executing {operation} query: {query}")
            logger.debug(f"With parameters: {params}")
            
            cursor.execute(query, params)
            
            if operation == 'search':
                results = cursor.fetchall()
                logger.debug(f"Search results: {results}")
                return results
            else:
                # For insert, update, delete, commit changes
                conn.commit()
                # If it's an insert with RETURNING, fetch the result
                if operation == 'insert' and 'RETURNING' in query.upper():
                    result = cursor.fetchone()
                    logger.debug(f"Insert result: {result}")
                    return result
                return None
                
    except psycopg2.Error as e:
        logger.error(f"Database error during {operation}: {str(e)}")
        logger.error(f"Query: {query}")
        logger.error(f"Parameters: {params}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during {operation}: {str(e)}")
        return None

def get_user_by_firebase_uid(firebase_uid):
    """Get user by Firebase UID"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                "SELECT * FROM users WHERE firebase_uid = %s",
                (firebase_uid,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting user by Firebase UID: {e}")
        return None

def get_user_by_email(email):
    """Get user by email"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def create_user(firebase_uid, username, email, password, **kwargs):
    """Create a new user"""
    try:
        with get_db_cursor() as (cursor, conn):
            # Build dynamic query based on provided fields
            fields = ['firebase_uid', 'username', 'email', 'password']
            values = [firebase_uid, username, email, password]
            
            for key, value in kwargs.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)
            
            placeholders = ', '.join(['%s'] * len(fields))
            field_names = ', '.join(fields)
            
            query = f"INSERT INTO users ({field_names}) VALUES ({placeholders}) RETURNING id"
            
            cursor.execute(query, values)
            result = cursor.fetchone()
            conn.commit()
            
            return result['id'] if result else None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None

def update_user_last_login(firebase_uid):
    """Update user's last login timestamp"""
    try:
        from datetime import datetime
        return execute_query(
            "update",
            "UPDATE users SET last_login = %s WHERE firebase_uid = %s",
            (datetime.utcnow(), firebase_uid)
        )
    except Exception as e:
        logger.error(f"Error updating last login: {e}")
        return None

def get_user_stokvels(firebase_uid):
    """Get stokvels where user is a member"""
    try:
        return execute_query(
            "search",
            """
            SELECT s.*, sm.role
            FROM stokvels s
            JOIN stokvel_members sm ON s.id = sm.stokvel_id
            WHERE sm.user_id = %s
            """,
            (firebase_uid,)
        )
    except Exception as e:
        logger.error(f"Error getting user stokvels: {e}")
        return []

def get_user_transactions(firebase_uid, limit=10):
    """Get user's recent transactions"""
    try:
        return execute_query(
            "search",
            """
            SELECT * FROM transactions
            WHERE user_id = %s
            ORDER BY transaction_date DESC
            LIMIT %s
            """,
            (firebase_uid, limit)
        )
    except Exception as e:
        logger.error(f"Error getting user transactions: {e}")
        return []

def verify_database_connection():
    """Verify database connection is working"""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        return False 