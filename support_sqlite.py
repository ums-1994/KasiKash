import os
import sqlite3
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

warnings.filterwarnings("ignore")

load_dotenv()

# SQLite database file
DB_FILE = "kasikash.db"

@contextmanager
def db_connection():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        print(f"Successfully connected to SQLite database: {DB_FILE}")
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
        query (str): The SQL query string with placeholders (?).
        params (tuple, optional): A tuple of values to substitute into the query.

    Returns:
        list: Results of the query for 'search' operation, otherwise None.
    """
    conn = None
    cur = None
    try:
        conn = sqlite3.connect(DB_FILE)
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

    except (sqlite3.Error, Exception) as e:
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

def close_db(connection=None, cursor=None):
    """
    close database connection
    :param connection:
    :param cursor:
    :return: close connection
    """
    cursor.close()
    connection.close()

def generate_df(df):
    """
    create new features
    :param df:
    :return: df
    """
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year
    df['Month_name'] = df['Date'].dt.month_name()
    df['Month'] = df['Date'].dt.month
    df['Day_name'] = df['Date'].dt.day_name()
    df['Day'] = df['Date'].dt.day
    df['Week'] = df['Date'].dt.isocalendar().week
    return df

def num2MB(num):
    """
        num: int, float
        it will return values like thousands(10K), Millions(10M),Billions(1B)
    """
    if num < 1000:
        return int(num)
    if 1000 <= num < 1000000:
        return f'{float("%.2f" % (num / 1000))}K'
    elif 1000000 <= num < 1000000000:
        return f'{float("%.2f" % (num / 1000000))}M'
    else:
        return f'{float("%.2f" % (num / 1000000000))}B'

# Initialize database with required tables
def init_database():
    """Initialize the SQLite database with required tables"""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    firebase_uid TEXT UNIQUE,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create stokvels table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stokvels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    purpose TEXT,
                    monthly_contribution REAL,
                    target_amount REAL,
                    target_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create stokvel_members table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stokvel_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stokvel_id INTEGER,
                    user_id INTEGER,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stokvel_id) REFERENCES stokvels (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create contributions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stokvel_id INTEGER,
                    user_id INTEGER,
                    amount REAL NOT NULL,
                    contribution_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stokvel_id) REFERENCES stokvels (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            print("✅ Database tables created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False

# Import all the plotting functions from the original support.py
# (These functions should work the same with SQLite)

def top_tiles(df=None):
    """Generate top tiles for dashboard"""
    if df is None:
        return []
    
    total_expense = df['Amount(₹)'].sum()
    total_income = df[df['Expense'] == 'Income']['Amount(₹)'].sum()
    total_expense_excluding_income = df[df['Expense'] != 'Income']['Amount(₹)'].sum()
    total_savings = total_income - total_expense_excluding_income
    
    tiles = [
        {'title': 'Total Income', 'value': f'₹{num2MB(total_income)}', 'color': 'success'},
        {'title': 'Total Expense', 'value': f'₹{num2MB(total_expense_excluding_income)}', 'color': 'danger'},
        {'title': 'Total Savings', 'value': f'₹{num2MB(total_savings)}', 'color': 'info'},
        {'title': 'Total Transactions', 'value': len(df), 'color': 'warning'}
    ]
    
    return tiles

def meraPie(df, names, values, hole=0, hole_text="", hole_font=14, height=200, width=200, margin=None):
    """Create a pie chart"""
    fig = px.pie(df, names=names, values=values, hole=hole, height=height, width=width)
    if hole_text:
        fig.add_annotation(text=hole_text, x=0.5, y=0.5, font=dict(size=hole_font), showarrow=False)
    if margin:
        fig.update_layout(margin=margin)
    return plot(fig, output_type='div', include_plotlyjs=False)

def meraBarChart(df=None, x=None, y=None, color=None, x_label=None, y_label=None, height=None, width=None,
                 show_legend=False, show_xtick=True, show_ytick=True, x_tickangle=0, y_tickangle=0, barmode='relative'):
    """Create a bar chart"""
    fig = px.bar(df, x=x, y=y, color=color, height=height, width=width, barmode=barmode)
    fig.update_layout(
        showlegend=show_legend,
        xaxis=dict(showticklabels=show_xtick, tickangle=x_tickangle),
        yaxis=dict(showticklabels=show_ytick, tickangle=y_tickangle)
    )
    if x_label:
        fig.update_xaxis(title=x_label)
    if y_label:
        fig.update_yaxis(title=y_label)
    return plot(fig, output_type='div', include_plotlyjs=False)

def meraLine(df, x, y, color, slider=False, show_legend=True, height=250):
    """Create a line chart"""
    fig = px.line(df, x=x, y=y, color=color, height=height)
    fig.update_layout(showlegend=show_legend)
    if slider:
        fig.update_xaxes(rangeslider_visible=True)
    return plot(fig, output_type='div', include_plotlyjs=False)

def meraScatter(df, x, y, color, y_label, slider=False, height=250):
    """Create a scatter plot"""
    fig = px.scatter(df, x=x, y=y, color=color, height=height)
    fig.update_yaxes(title=y_label)
    if slider:
        fig.update_xaxes(rangeslider_visible=True)
    return plot(fig, output_type='div', include_plotlyjs=False)

def meraHeatmap(df, x, y, height=250, title=""):
    """Create a heatmap"""
    pivot_table = df.pivot_table(index=y, columns=x, aggfunc='size', fill_value=0)
    fig = px.imshow(pivot_table, height=height, title=title)
    return plot(fig, output_type='div', include_plotlyjs=False)

def month_bar(df, height=250):
    """Create a monthly bar chart"""
    monthly_data = df.groupby('Month_name')['Amount(₹)'].sum().reset_index()
    fig = px.bar(monthly_data, x='Month_name', y='Amount(₹)', height=height)
    return plot(fig, output_type='div', include_plotlyjs=False)

def meraSunburst(df, height=300):
    """Create a sunburst chart"""
    fig = px.sunburst(df, path=['Expense', 'Note'], values='Amount(₹)', height=height)
    return plot(fig, output_type='div', include_plotlyjs=False)

def get_user_data(user_id):
    """Get user data by user_id"""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE firebase_uid = ?", (user_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None 