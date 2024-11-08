import pandas as pd
import numpy as np
from utils.database import get_sqlalchemy_engine
from datetime import datetime
from sqlalchemy import text

def calculate_total_members():
    try:
        engine = get_sqlalchemy_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM members WHERE active = TRUE"))
            total = result.scalar()
            return total
    except Exception as e:
        print(f"Error calculating total members: {str(e)}")
        return 0

def calculate_monthly_revenue():
    try:
        engine = get_sqlalchemy_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COALESCE(SUM(amount), 0)
                FROM transactions 
                WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE)
            """))
            revenue = result.scalar() or 0
            return float(revenue)
    except Exception as e:
        print(f"Error calculating monthly revenue: {str(e)}")
        return 0.0

def calculate_member_kpis(period):
    try:
        engine = get_sqlalchemy_engine()
        
        # Calculate growth rate
        growth_query = """
            SELECT 
                DATE_TRUNC('month', join_date) as month,
                COUNT(*) as new_members
            FROM members
            GROUP BY DATE_TRUNC('month', join_date)
            ORDER BY month
        """
        growth_data = pd.read_sql(text(growth_query), engine)
        
        # Calculate retention rate with zero handling
        retention_query = """
            WITH member_counts AS (
                SELECT 
                    COUNT(*) as total_members,
                    COUNT(*) FILTER (WHERE active = TRUE) as active_members
                FROM members
            )
            SELECT 
                CASE 
                    WHEN total_members = 0 THEN 0
                    ELSE (active_members * 100.0 / total_members)
                END as retention_rate
            FROM member_counts
        """
        retention_data = pd.read_sql(text(retention_query), engine)
        
        return {
            'growth_rate': calculate_growth_rate(growth_data),
            'growth_rate_change': calculate_growth_rate_change(growth_data),
            'retention_rate': retention_data['retention_rate'].iloc[0] if not retention_data.empty else 0,
            'retention_rate_change': 0,
            'growth_data': growth_data,
            'distribution_data': calculate_member_distribution()
        }
    except Exception as e:
        print(f"Error calculating member KPIs: {str(e)}")
        return {
            'growth_rate': 0,
            'growth_rate_change': 0,
            'retention_rate': 0,
            'retention_rate_change': 0,
            'growth_data': pd.DataFrame(),
            'distribution_data': pd.DataFrame()
        }

def calculate_growth_rate(data):
    if len(data) < 2:
        return 0
    if data['new_members'].iloc[0] == 0:
        return 100  # Represent infinite growth as 100%
    return ((data['new_members'].iloc[-1] - data['new_members'].iloc[0]) / 
            data['new_members'].iloc[0] * 100)

def calculate_growth_rate_change(data):
    if len(data) < 3:
        return 0
    current_growth = calculate_growth_rate(data.iloc[-2:])
    previous_growth = calculate_growth_rate(data.iloc[-3:-1])
    return current_growth - previous_growth

def calculate_member_distribution():
    try:
        engine = get_sqlalchemy_engine()
        query = """
            SELECT country, COUNT(*) as count
            FROM members
            WHERE active = TRUE
            GROUP BY country
        """
        distribution = pd.read_sql(text(query), engine)
        return distribution
    except Exception as e:
        print(f"Error calculating member distribution: {str(e)}")
        return pd.DataFrame(columns=['country', 'count'])

def calculate_operating_margin():
    engine = get_sqlalchemy_engine()
    
    # Get total revenue
    revenue_query = "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE amount > 0"
    with engine.connect() as conn:
        total_revenue = conn.execute(text(revenue_query)).scalar() or 0
    
    # Get total expenses
    expenses_query = "SELECT COALESCE(SUM(ABS(amount)), 0) FROM transactions WHERE amount < 0"
    with engine.connect() as conn:
        total_expenses = conn.execute(text(expenses_query)).scalar() or 0
    
    if total_revenue == 0:
        return 0
    
    return ((total_revenue - total_expenses) / total_revenue) * 100

def calculate_event_metrics(period):
    engine = get_sqlalchemy_engine()
    
    attendance_query = """
        SELECT 
            name,
            date,
            revenue / NULLIF(50, 0) as attendance
        FROM events
        ORDER BY date
    """
    attendance_data = pd.read_sql(text(attendance_query), engine)
    
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
    revenue_data = pd.read_sql(text(revenue_query), engine)
    
    return {
        'attendance_data': attendance_data,
        'revenue_data': revenue_data
    }

def calculate_revenue_forecast(annual_fee, event_fee, num_events, scenario='realistic'):
    """Calculate revenue forecast based on different growth scenarios"""
    try:
        growth_multipliers = {
            'pessimistic': 0.5,
            'realistic': 1.0,
            'optimistic': 1.5
        }
        
        multiplier = growth_multipliers[scenario]
        
        # Initialize with default values
        current_members = {'Netherlands': 135, 'Belgium': 26, 'Germany': 0}
        
        try:
            # Try to get actual numbers from database
            engine = get_sqlalchemy_engine()
            with engine.connect() as conn:
                member_query = """
                    SELECT country, COUNT(*) as count
                    FROM members
                    WHERE active = TRUE
                    GROUP BY country
                """
                result = conn.execute(text(member_query))
                db_members = dict(result.fetchall())
            
            # Update defaults with actual values if available
            current_members.update(db_members)
        except Exception as e:
            print(f"Warning: Using default member counts due to database error: {str(e)}")
        
        # Get growth rates from config
        from utils.config import load_config
        config = load_config()
        growth_targets = config['growth_targets']
        
        # Calculate 12-month forecast using ME (month end) frequency
        months = pd.date_range(pd.Timestamp.now(), periods=12, freq='ME')
        forecast = pd.DataFrame(index=months)
        
        for country in ['Netherlands', 'Belgium', 'Germany']:
            members = float(current_members.get(country, 0))
            monthly_growth = []
            
            for _ in range(12):
                if country == 'Germany':
                    # Absolute growth for Germany
                    growth = float(growth_targets[country]) * multiplier
                else:
                    # Percentage growth for Netherlands and Belgium
                    growth_rate = float(growth_targets[country]) / 100
                    growth = members * growth_rate * multiplier
                
                members += growth
                monthly_growth.append(members)
            
            forecast[f'{country}_members'] = monthly_growth
        
        # Calculate revenue components
        forecast['total_members'] = forecast[[f'{c}_members' for c in ['Netherlands', 'Belgium', 'Germany']]].sum(axis=1)
        forecast['membership_revenue'] = forecast['total_members'] * (annual_fee / 12)
        forecast['event_revenue'] = forecast['total_members'] * event_fee * (num_events / 12)
        forecast['total_revenue'] = forecast['membership_revenue'] + forecast['event_revenue']
        
        return forecast
    except Exception as e:
        print(f"Error in revenue forecast calculation: {str(e)}")
        return pd.DataFrame(columns=['total_members', 'membership_revenue', 'event_revenue', 'total_revenue'])

def calculate_expenses_forecast(marketing_percentage, base_salary, num_employees, num_events, event_fee, scenario='realistic'):
    """Calculate expense forecast based on different scenarios"""
    try:
        expense_multipliers = {
            'pessimistic': 1.2,  # Higher expenses
            'realistic': 1.0,
            'optimistic': 0.9    # Lower expenses
        }
        
        multiplier = expense_multipliers[scenario]
        
        # Get current revenue for marketing budget calculation
        revenue = max(calculate_monthly_revenue() * 12, 1000)  # Minimum 1000 to avoid zero
        total_members = max(calculate_total_members(), 1)  # Minimum 1 to avoid zero
        
        expenses = {
            'Marketing': (revenue * marketing_percentage / 100) * multiplier,
            'Salaries': (base_salary * num_employees * 12) * multiplier,
            'Events': (total_members * event_fee * num_events) * multiplier,
            'Operations': 180000 * multiplier  # Base yearly operational costs
        }
        
        return expenses
    except Exception as e:
        print(f"Error in expenses forecast calculation: {str(e)}")
        return {'Marketing': 0, 'Salaries': 0, 'Events': 0, 'Operations': 0}

def calculate_cashflow(revenue_forecast, expenses, scenario='realistic'):
    """Calculate cash flow based on revenue and expense forecasts"""
    try:
        cashflow = revenue_forecast.copy()
        
        # Monthly expenses
        monthly_expenses = sum(expenses.values()) / 12
        cashflow['expenses'] = monthly_expenses
        cashflow['net_cashflow'] = cashflow['total_revenue'] - monthly_expenses
        cashflow['cumulative_cashflow'] = cashflow['net_cashflow'].cumsum()
        
        return cashflow
    except Exception as e:
        print(f"Error in cashflow calculation: {str(e)}")
        return pd.DataFrame(columns=['expenses', 'net_cashflow', 'cumulative_cashflow'])