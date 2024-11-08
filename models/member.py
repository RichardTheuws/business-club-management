from utils.database import get_sqlalchemy_engine, get_session
import pandas as pd
from sqlalchemy import text

def add_member(name, email, country, join_date, membership_type):
    engine = get_sqlalchemy_engine()
    
    try:
        with engine.connect() as conn:
            # Insert member
            result = conn.execute(
                text("""
                    INSERT INTO members (name, email, country, join_date, membership_type)
                    VALUES (:name, :email, :country, :join_date, :membership_type)
                    RETURNING id
                """),
                {
                    "name": name,
                    "email": email,
                    "country": country,
                    "join_date": join_date,
                    "membership_type": membership_type
                }
            )
            member_id = result.scalar()
            
            # Add initial membership fee transaction
            conn.execute(
                text("""
                    INSERT INTO transactions (member_id, amount, transaction_type, transaction_date)
                    VALUES (:member_id, :amount, :transaction_type, :transaction_date)
                """),
                {
                    "member_id": member_id,
                    "amount": 795,
                    "transaction_type": "membership_fee",
                    "transaction_date": join_date
                }
            )
            
            conn.commit()
            return True
    except Exception as e:
        print(f"Error adding member: {str(e)}")
        return False

def get_members_by_country(country):
    try:
        engine = get_sqlalchemy_engine()
        query = text("""
            SELECT 
                id,
                name,
                email,
                join_date,
                membership_type
            FROM members
            WHERE country = :country AND active = TRUE
            ORDER BY join_date DESC
        """)
        
        with engine.connect() as conn:
            result = pd.read_sql(query, conn, params={"country": country})
        return result
    except Exception as e:
        print(f"Error getting members: {str(e)}")
        return pd.DataFrame()

def update_member_status(member_id, active):
    engine = get_sqlalchemy_engine()
    
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE members
                    SET active = :active
                    WHERE id = :member_id
                """),
                {"active": active, "member_id": member_id}
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating member status: {str(e)}")
        return False
