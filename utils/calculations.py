import pandas as pd
import numpy as np
from utils.database import get_db_connection

def calculate_total_members():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM members WHERE active = TRUE")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total

def calculate_monthly_revenue():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(amount) 
        FROM transactions 
        WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
    """)
    revenue = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return revenue

def calculate_member_kpis(period):
    conn = get_db_connection()
    
    # Calculate growth rate
    growth_query = """
        SELECT 
            DATE_TRUNC('month', join_date) as month,
            COUNT(*) as new_members
        FROM members
        GROUP BY DATE_TRUNC('month', join_date)
        ORDER BY month
    """
    growth_data = pd.read_sql(growth_query, conn)
    
    # Calculate retention rate
    retention_query = """
        SELECT 
            COUNT(*) FILTER (WHERE active = TRUE) * 100.0 / COUNT(*) as retention_rate
        FROM members
    """
    retention_data = pd.read_sql(retention_query, conn)
    
    conn.close()
    
    return {
        'growth_rate': calculate_growth_rate(growth_data),
        'growth_rate_change': calculate_growth_rate_change(growth_data),
        'retention_rate': retention_data['retention_rate'].iloc[0],
        'retention_rate_change': 0,  # Calculate based on historical data
        'growth_data': growth_data,
        'distribution_data': calculate_member_distribution()
    }

def calculate_financial_kpis(period):
    conn = get_db_connection()
    
    # Revenue per member
    revenue_query = """
        SELECT 
            m.id,
            SUM(t.amount) as revenue
        FROM members m
        LEFT JOIN transactions t ON m.id = t.member_id
        GROUP BY m.id
    """
    revenue_data = pd.read_sql(revenue_query, conn)
    
    conn.close()
    
    return {
        'revenue_per_member': revenue_data['revenue'].mean(),
        'revenue_per_member_change': 0,  # Calculate based on historical data
        'operating_margin': calculate_operating_margin(),
        'operating_margin_change': 0,  # Calculate based on historical data
        'financial_data': create_financial_summary(),
        'cash_flow_data': create_cash_flow_summary()
    }

def calculate_growth_rate(data):
    if len(data) < 2:
        return 0
    return ((data['new_members'].iloc[-1] - data['new_members'].iloc[0]) / 
            data['new_members'].iloc[0] * 100)

def calculate_growth_rate_change(data):
    if len(data) < 3:
        return 0
    current_growth = calculate_growth_rate(data.iloc[-2:])
    previous_growth = calculate_growth_rate(data.iloc[-3:-1])
    return current_growth - previous_growth

def calculate_member_distribution():
    conn = get_db_connection()
    query = """
        SELECT country, COUNT(*) as count
        FROM members
        WHERE active = TRUE
        GROUP BY country
    """
    distribution = pd.read_sql(query, conn)
    conn.close()
    return distribution

def calculate_operating_margin():
    conn = get_db_connection()
    
    # Get total revenue
    revenue_query = "SELECT SUM(amount) FROM transactions WHERE amount > 0"
    cur = conn.cursor()
    cur.execute(revenue_query)
    total_revenue = cur.fetchone()[0] or 0
    
    # Get total expenses
    expenses_query = "SELECT SUM(amount) FROM transactions WHERE amount < 0"
    cur.execute(expenses_query)
    total_expenses = abs(cur.fetchone()[0] or 0)
    
    cur.close()
    conn.close()
    
    if total_revenue == 0:
        return 0
    
    return ((total_revenue - total_expenses) / total_revenue) * 100

def calculate_event_metrics(period):
    conn = get_db_connection()
    
    attendance_query = """
        SELECT 
            name,
            date,
            revenue / 50 as attendance  -- Assuming €50 per attendee
        FROM events
        ORDER BY date
    """
    attendance_data = pd.read_sql(attendance_query, conn)
    
    revenue_query = """
        SELECT 
            name,
            date,
            revenue,
            costs,
            revenue - costs as profit
        FROM events
        ORDER BY date
    """
    revenue_data = pd.read_sql(revenue_query, conn)
    
    conn.close()
    
    return {
        'attendance_data': attendance_data,
        'revenue_data': revenue_data
    }
