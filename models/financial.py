from utils.database import get_sqlalchemy_engine
import pandas as pd
from sqlalchemy import text

def record_transaction(member_id, amount, transaction_type, transaction_date):
    engine = get_sqlalchemy_engine()
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO transactions 
                    (member_id, amount, transaction_type, transaction_date)
                    VALUES (:member_id, :amount, :transaction_type, :transaction_date)
                    RETURNING id
                """),
                {
                    "member_id": member_id,
                    "amount": amount,
                    "transaction_type": transaction_type,
                    "transaction_date": transaction_date
                }
            )
            
            transaction_id = result.scalar()
            conn.commit()
            return transaction_id
    except Exception as e:
        print(f"Error recording transaction: {str(e)}")
        return None

def get_financial_summary(start_date, end_date):
    try:
        engine = get_sqlalchemy_engine()
        query = text("""
            SELECT 
                DATE_TRUNC('month', transaction_date) as month,
                transaction_type,
                SUM(amount) as total_amount
            FROM transactions
            WHERE transaction_date BETWEEN :start_date AND :end_date
            GROUP BY DATE_TRUNC('month', transaction_date), transaction_type
            ORDER BY month, transaction_type
        """)
        
        with engine.connect() as conn:
            summary = pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
        return summary
    except Exception as e:
        print(f"Error getting financial summary: {str(e)}")
        return pd.DataFrame()

def record_event(name, date, country, revenue, costs):
    engine = get_sqlalchemy_engine()
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO events 
                    (name, date, country, revenue, costs)
                    VALUES (:name, :date, :country, :revenue, :costs)
                    RETURNING id
                """),
                {
                    "name": name,
                    "date": date,
                    "country": country,
                    "revenue": revenue,
                    "costs": costs
                }
            )
            
            event_id = result.scalar()
            conn.commit()
            return event_id
    except Exception as e:
        print(f"Error recording event: {str(e)}")
        return None
