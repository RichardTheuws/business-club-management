from utils.database import get_db_connection
import pandas as pd

def record_transaction(member_id, amount, transaction_type, transaction_date):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO transactions 
            (member_id, amount, transaction_type, transaction_date)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (member_id, amount, transaction_type, transaction_date))
        
        transaction_id = cur.fetchone()[0]
        conn.commit()
        return transaction_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_financial_summary(start_date, end_date):
    conn = get_db_connection()
    query = """
        SELECT 
            DATE_TRUNC('month', transaction_date) as month,
            transaction_type,
            SUM(amount) as total_amount
        FROM transactions
        WHERE transaction_date BETWEEN %s AND %s
        GROUP BY DATE_TRUNC('month', transaction_date), transaction_type
        ORDER BY month, transaction_type
    """
    
    summary = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    return summary

def record_event(name, date, country, revenue, costs):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO events 
            (name, date, country, revenue, costs)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (name, date, country, revenue, costs))
        
        event_id = cur.fetchone()[0]
        conn.commit()
        return event_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
