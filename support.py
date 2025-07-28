import os
import psycopg2
from dotenv import load_dotenv
from contextlib import contextmanager
import datetime
import pandas as pd
import plotly
import plotly.express as px
import json
import warnings
import plotly.graph_objects as go
from plotly.offline import plot
from support_postgres import generate_df

warnings.filterwarnings("ignore")

load_dotenv()

# Database connection parameters
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

@contextmanager
def db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = False
        print(f"Successfully connected to database: {DB_NAME}")
        yield conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise e
    finally:
        if 'conn' in locals():
            conn.close()

@contextmanager
def db_cursor():
    with db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

def verify_db_connection():
    """Verify database connection and return True if successful"""
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

def execute_query(operation, query, params=None):
    """
    Executes a database query or command.

    Args:
        operation (str): 'search', 'insert', 'update', or 'delete'.
        query (str): The SQL query string with placeholders (%s).
        params (tuple, optional): A tuple of values to substitute into the query.

    Returns:
        list: Results of the query for 'search' operation, otherwise None.
    """
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()

        print(f"Executing {operation} query: {query}")
        print(f"With parameters: {params}")
        
        cur.execute(query, params)

        if operation == 'search':
            results = cur.fetchall()
            print(f"Search results: {results}")
            return results
        else:
            # For insert, update, delete, commit changes
            conn.commit()
            # If it's an insert with RETURNING, fetch the result
            if operation == 'insert' and 'RETURNING' in query.upper():
                result = cur.fetchone()
                print(f"Insert result: {result}")
                if result is None:
                    print("Warning: No result returned from RETURNING clause")
                return result
            return None # Return None for other operations

    except (psycopg2.Error, Exception) as e:
        if conn:
            conn.rollback()
        print(f"Database error during {operation}: {str(e)}")
        print(f"Query: {query}")
        print(f"Parameters: {params}")
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close() 


def save_statement_analysis(conn, user_id, statement_text, ai_analysis, transactions, file_name, ai_budget_plan):
    """
    Save a financial statement analysis to the database.
    Args:
        conn: psycopg2 connection object
        user_id (str): Firebase UID of the user
        statement_text (str): Raw statement text
        ai_analysis (str): AI-generated analysis
        transactions (list/dict): Parsed transactions (will be stored as JSON)
        file_name (str): Name of the uploaded file
        ai_budget_plan (str): AI-generated budget plan
    Returns:
        int: The id of the inserted analysis row
    """
    import json
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO financial_statement_analysis
                    (user_id, statement_text, ai_analysis, transactions_json, file_name, ai_budget_plan)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (user_id, statement_text, ai_analysis, json.dumps(transactions), file_name, ai_budget_plan)
            )
            analysis_id = cur.fetchone()[0]
            conn.commit()
            return analysis_id
    except Exception as e:
        print(f"[ERROR] Failed to save statement analysis: {e}")
        conn.rollback()
        return None 


def get_latest_analysis(conn, user_id, with_budget=False):
    """
    Get the latest financial statement analysis for a user.
    """
    try:
        with conn.cursor() as cur:
            query = """
                SELECT id, statement_text, ai_analysis, transactions_json, ai_budget_plan
                FROM financial_statement_analysis
                WHERE user_id = %s
                ORDER BY uploaded_at DESC
                LIMIT 1
            """
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            if result and with_budget:
                return result
            elif result:
                # return without budget if not requested
                return result[0], result[1], result[2], result[3], None
            return None
    except Exception as e:
        print(f"[ERROR] Failed to get latest analysis: {e}")
        return None


def save_advisor_chat(conn, user_id, analysis_id, message, response):
    """
    Save a financial advisor chat message to the database.
    """
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO financial_advisor_chat
                    (user_id, statement_analysis_id, message, response)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, analysis_id, message, response)
            )
            conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to save advisor chat: {e}")
        conn.rollback() 