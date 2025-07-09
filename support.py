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
from psycopg2.extras import Json

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

def save_statement_analysis(conn, user_id, statement_text, ai_analysis, transactions, file_name, ai_budget_plan=None):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO financial_statement_analysis
            (user_id, statement_text, ai_analysis, transactions_json, file_name, ai_budget_plan)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, statement_text, ai_analysis, Json(transactions), file_name, ai_budget_plan)
        )
        analysis_id = cur.fetchone()[0]
        conn.commit()
        return analysis_id

def get_latest_analysis(conn, user_id, with_budget=False):
    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM financial_statement_analysis")
        all_user_ids = cur.fetchall()
        print(f"[DEBUG] All user_ids in financial_statement_analysis: {all_user_ids}", flush=True)
        print(f"[DEBUG] get_latest_analysis query param: {user_id}", flush=True)
        if with_budget:
            cur.execute(
                """
                SELECT id, statement_text, ai_analysis, transactions_json, ai_budget_plan
                FROM financial_statement_analysis
                WHERE user_id = %s
                ORDER BY uploaded_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            return cur.fetchone()  # (id, statement_text, ai_analysis, transactions_json, ai_budget_plan)
        else:
            cur.execute(
                """
                SELECT id, statement_text, ai_analysis
                FROM financial_statement_analysis
                WHERE user_id = %s
                ORDER BY uploaded_at DESC
                LIMIT 1
                """,
                (user_id,)
            )
            return cur.fetchone()  # (id, statement_text, ai_analysis)

def save_advisor_chat(conn, user_id, analysis_id, message, response):
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