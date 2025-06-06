import os
import psycopg2
from dotenv import load_dotenv
from contextlib import contextmanager
import datetime
import pandas as pd
# import mysql.connector  # pip install mysql-connector-python
import plotly
import plotly.express as px
import json
import warnings
import plotly.graph_objects as go
from plotly.offline import plot

warnings.filterwarnings("ignore")

load_dotenv()

# Database connection parameters
DB_NAME = 'kasikash'
DB_USER = 'postgres'
DB_PASSWORD = '12345'
DB_HOST = 'localhost'
DB_PORT = '5432'

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


# Use this function for SQLITE3
# def connect_db():
#     conn = sqlite3.connect("expense.db")
#     cur = conn.cursor()
#     cur.execute(
#         '''CREATE TABLE IF NOT EXISTS user_login (user_id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(30) NOT NULL, 
#         email VARCHAR(30) NOT NULL UNIQUE, password VARCHAR(20) NOT NULL)''')
#     cur.execute(
#         '''CREATE TABLE IF NOT EXISTS user_expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, pdate DATE NOT 
#         NULL, expense VARCHAR(10) NOT NULL, amount INTEGER NOT NULL, pdescription VARCHAR(50), FOREIGN KEY (user_id) 
#         REFERENCES user_login(user_id))''')
#     conn.commit()
#     return conn, cur


# Use this function for mysql
# import mysql.connector  # pip install mysql-connector-python
# def connect_db(host="localhost", user="root", passwd="123456", port=3306, database='expense',
#                auth_plugin='mysql_native_password'):
#     """
#     Connect to database
#     :param host: host
#     :param user: username
#     :param passwd: password
#     :param port: port no
#     :param database: database name
#     :param auth_plugin: plugin
#     :return: connection, cursor
#     """
#     conn = mysql.connector.connect(host=host, user=user, passwd=passwd, port=port, database=database,
#                                    auth_plugin=auth_plugin)
#     cursor = conn.cursor()
#     return conn, cursor


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


def top_tiles(df=None):
    """
    Sum of total expenses
    :param df:
    :return: sum (as numerical values)
    """
    if df is not None:
        tiles_data = df[['Expense', 'Amount']].groupby('Expense').sum()
        # Initialize tiles with numerical values (0)
        tiles = {'Earning': 0.0, 'Investment': 0.0, 'Saving': 0.0, 'Spend': 0.0} # Use floats for potential decimal amounts
        for expense_type in ['Earning', 'Investment', 'Saving', 'Spend']:
            if expense_type in tiles_data.index:
                try:
                    # Store the raw numerical amount directly
                    tiles[expense_type] = float(tiles_data.loc[expense_type]['Amount'])
                except Exception as e:
                    print(f"Error processing amount for {expense_type}: {e}")
                    tiles[expense_type] = 0.0 # Default to 0.0 if there's an issue

        # Return numerical values
        return tiles['Earning'], tiles['Spend'], tiles['Investment'], tiles['Saving']
    # Return default numerical values if df is None
    return 0.0, 0.0, 0.0, 0.0


def generate_Graph(df=None):
    """
    create graph
    :param df: Dataframe
    :return:
    """
    if df is not None and df.shape[0] > 0:
        # Bar_chart
        bar_data = df[['Expense', 'Amount']].groupby('Expense').sum().reset_index()
        bar = px.bar(x=bar_data['Expense'], y=bar_data['Amount'], color=bar_data['Expense'], template="plotly_dark",
                     labels={'x': 'Expense Type', 'y': 'Balance (₹)'}, height=287)
        bar.update(layout_showlegend=False)
        bar.update_layout(
            margin=dict(l=2, r=2, t=40, b=2),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)')

        # Stacked Bar Chart
        s = df.groupby(['Note', 'Expense']).sum().reset_index()
        stack = px.bar(x=s['Note'], y=s['Amount'], color=s['Expense'], barmode="stack", template="plotly_dark",
                       labels={'x': 'Category', 'y': 'Balance (₹)'}, height=290)
        stack.update(layout_showlegend=False)
        stack.update_xaxes(tickangle=45)
        stack.update_layout(
            margin=dict(l=2, r=2, t=30, b=2),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )

        # Line Chart
        line = px.line(df, x='Date', y='Amount', color='Expense', template="plotly_dark")
        line.update_xaxes(rangeslider_visible=True)
        line.update_layout(title_text='Track Record', title_x=0.,
                           legend=dict(
                               orientation="h",
                               yanchor="bottom",
                               y=1.02,
                               xanchor="right",
                               x=1
                           ),
                           margin=dict(l=2, r=2, t=30, b=2),
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                           )

        # Sunburst pie chart
        pie = px.sunburst(df, path=['Expense', 'Note'], values='Amount', height=280, template="plotly_dark")
        pie.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

        bar = json.dumps(bar, cls=plotly.utils.PlotlyJSONEncoder)
        pie = json.dumps(pie, cls=plotly.utils.PlotlyJSONEncoder)
        line = json.dumps(line, cls=plotly.utils.PlotlyJSONEncoder)
        stack_bar = json.dumps(stack, cls=plotly.utils.PlotlyJSONEncoder)

        return bar, pie, line, stack_bar
    return None


def makePieChart(df=None, expense='Earning', names='Note', values='Amount', hole=0.5,
                 color_discrete_sequence=px.colors.sequential.RdBu, size=300, textposition='inside',
                 textinfo='percent+label', margin=2):
    fig = px.pie(df[df['Expense'] == expense], names=names, values=values, hole=hole,
                 color_discrete_sequence=color_discrete_sequence, height=size, width=size)
    fig.update_traces(textposition=textposition, textinfo=textinfo)
    fig.update_layout(annotations=[dict(text=expense, y=0.5, font_size=20, font_color='white', showarrow=False)])
    fig.update_layout(margin=dict(l=margin, r=margin, t=margin, b=margin),
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    fig.update(layout_showlegend=False)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def meraBarChart(df=None, x=None, y=None, color=None, x_label=None, y_label=None, height=None, width=None,
                 show_legend=False, show_xtick=True, show_ytick=True, x_tickangle=0, y_tickangle=0, barmode='relative'):
    bar = px.bar(data_frame=df, x=x, y=y, color=color, template="plotly_dark", barmode=barmode,
                 labels={'x': x_label, 'y': y_label}, height=height, width=width)
    bar.update(layout_showlegend=show_legend)
    bar.update_layout(
        margin=dict(l=2, r=2, t=2, b=2),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)')
    bar.update_layout(xaxis=dict(showticklabels=show_xtick, tickangle=x_tickangle),
                      yaxis=dict(showticklabels=show_ytick, tickangle=y_tickangle))

    return json.dumps(bar, cls=plotly.utils.PlotlyJSONEncoder)


def get_monthly_data(df, year=datetime.datetime.today().year, res='int'):
    """
    Data table
    :param res:
    :param df: Dataframe
    :param year: present year
    :return: list of dictionary
    """
    temp = pd.DataFrame()
    d_year = df.groupby('Year').get_group(year)[['Expense', 'Amount', 'Month']]
    d_month = d_year.groupby("Month")
    for month in list(d_month.groups.keys())[::-1][:3]:
        dexp = d_month.get_group(month).groupby('Expense').sum().reset_index()
        for row in range(dexp.shape[0]):
            temp = temp.append(
                dict({"Expense": dexp.iloc[row]['Expense'], "Amount": dexp.iloc[row]['Amount'], "Month": month}),
                ignore_index=True)
    month_name = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 7: "July", 8: 'August',
                  9: "September", 10: "October", 11: "November", 12: "December"}
    ls = []
    for month in list(d_month.groups.keys())[::-1][:3]:
        m = {}
        s = temp[temp['Month'] == month]
        m['Month'] = month_name[month]
        for i in range(s.shape[0]):
            if res == 'int':
                m[s.iloc[i]['Expense']] = int(s.iloc[i]['Amount'])
            else:
                m[s.iloc[i]['Expense']] = num2MB(int(s.iloc[i]['Amount']))
        ls.append(m)
    return ls


def sort_summary(df):
    """
    Generate data for cards
    :param df: Dataframe
    :return: list of dictionary
    """
    datas = []

    h_month, h_year, h_amount = [], [], []
    for year in list(df['Year'].unique()):
        d = df[df['Year'] == year]
        data = d[d['Expense'] == 'Earning'].groupby("Month_name").sum()['Amount'].reset_index().sort_values("Amount",
                                                                                                            ascending=False).iloc[
            0]
        h_month.append(data['Month_name'])
        h_year.append(year)
        h_amount.append(data['Amount'])
    amount = max(h_amount)
    month = h_month[h_amount.index(amount)]
    year = h_year[h_amount.index(amount)]
    datas.append(
        {'head': "₹" + str(num2MB(amount)), 'main': f"{month}'{str(year)[2:]}", 'msg': "Highest income in a month"})

    # per day avg income
    per_day_income = df[df['Expense'] == 'Earning']['Amount'].sum() / df['Date'].nunique()
    datas.append({'head': 'Income', 'main': "₹" + str(num2MB(per_day_income)), 'msg': "You earn everyday"})

    # per week avg spend
    per_week_saving = df[df['Expense'] == 'Saving'].groupby('Week').sum()['Amount'].mean()
    datas.append({'head': 'Saving', 'main': "₹" + str(num2MB(per_week_saving)), 'msg': "You save every week"})

    # per month income
    avg_earn = df[df['Expense'] == 'Earning'].groupby('Month').sum()['Amount'].reset_index()['Amount'].mean()
    # per month spend
    avg_spd = df[df['Expense'] == 'Spend'].groupby('Month').sum()['Amount'].reset_index()['Amount'].mean()

    # per month avg spend % wrt income
    monthly_spend = (avg_spd / avg_earn) * 100
    datas.append({'head': 'Spend', 'main': f"{round(monthly_spend, 2)}%", 'msg': "You spend every month"})

    # every minute invest
    every_minute_invest = round(df[df['Expense'] == 'Investment'].groupby('Day').sum()['Amount'].mean() / 24 / 60, 2)
    datas.append({'head': 'Invest', 'main': f"₹{round(every_minute_invest, 2)}", 'msg': "You invest every minute"})

    return datas


def expense_goal(df):
    """
    Monthly goal data
    :param df: Dataframe
    :return: list of dictionary
    """
    goal_ls = []
    for expense in list(df['Expense'].unique()):
        dic = {'type': expense}
        a = get_monthly_data(df, res='int')
        x = []
        for i in a[:2]:
            x.append(i[expense])
        first, second = x[0], x[1]
        diff = int(first) - int(second)
        percent = round((diff / second) * 100, 1)
        if percent > 0:
            dic['status'] = 'increased'
        else:
            dic['status'] = 'decreased'
        dic['percent'] = abs(percent)
        dic['value'] = "₹" + num2MB(x[0])
        goal_ls.append(dic)
    return goal_ls


# --------------- Analysis -----------------
def meraPie(df, names, values, hole=0, hole_text="", hole_font=14, height=200, width=200, margin=None):
    """Generates a Plotly Pie Chart."""
    fig = px.pie(df, names=names, values=values, hole=hole, height=height, width=width, margin=margin)
    fig.update_traces(textinfo="percent+label", insidetextorientation="radial")
    if hole > 0 and hole_text:
        fig.add_annotation(text=hole_text, x=0.5, y=0.5, showarrow=False, font=dict(size=hole_font))
    fig.update_layout(showlegend=True, font=dict(size=10))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def meraLine(df, x, y, color, slider=False, show_legend=True, height=250):
    """Generates a Plotly Line Chart."""
    fig = px.line(df, x=x, y=y, color=color, height=height)
    fig.update_layout(xaxis_title=x, yaxis_title=y, showlegend=show_legend, font=dict(size=10))
    if slider:
        fig.update_layout(xaxis=dict(rangeslider=dict(visible=True)))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def meraScatter(df, x, y, color, y_label, slider=False, height=250):
    """Generates a Plotly Scatter Plot."""
    fig = px.scatter(df, x=x, y=y, color=color, height=height)
    fig.update_layout(xaxis_title=x, yaxis_title=y_label, font=dict(size=10))
    if slider:
        fig.update_layout(xaxis=dict(rangeslider=dict(visible=True)))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def meraHeatmap(df, x, y, height=250, title=""):
    """Generates a Plotly Heatmap."""
    fig = px.density_heatmap(df, x=x, y=y, height=height, title=title)
    fig.update_layout(xaxis_title=x, yaxis_title=y, font=dict(size=10))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def month_bar(df, height=250):
    """Generates a monthly bar chart."""
    df["month_name"] = df["Date"].dt.strftime("%b")
    df3 = df.groupby(["month_name", 'Expense']).sum().reset_index()
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df3["month_name"] = pd.Categorical(df3["month_name"], categories=month_order, ordered=True)
    df3 = df3.sort_values("month_name")
    fig = px.bar(df3, x='month_name', y='Amount(₹)', color='Expense', height=height)
    fig.update_layout(xaxis_title="Month", yaxis_title="Total Amount(₹)", font=dict(size=10))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def meraSunburst(df, height=300):
    """Generates a Plotly Sunburst Chart."""
    fig = px.sunburst(df, path=['Expense', 'Note'], values='Amount(₹)', height=height)
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), font=dict(size=10))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plot_div


def get_user_data(user_id):
    """Fetches user data by user ID."""
    query = "SELECT id, username, email FROM users WHERE id = %s"
    user_data = execute_query('search', query, (user_id,))
    if user_data:
        return dict(zip(['id', 'username', 'email'], user_data[0]))
    return None
