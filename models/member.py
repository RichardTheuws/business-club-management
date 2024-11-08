from utils.database import get_db_connection
import pandas as pd

def add_member(name, email, country, join_date, membership_type):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO members (name, email, country, join_date, membership_type)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (name, email, country, join_date, membership_type))
        
        member_id = cur.fetchone()[0]
        
        # Add initial membership fee transaction
        cur.execute("""
            INSERT INTO transactions (member_id, amount, transaction_type, transaction_date)
            VALUES (%s, %s, %s, %s)
        """, (member_id, 795, 'membership_fee', join_date))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_members_by_country(country):
    conn = get_db_connection()
    query = """
        SELECT 
            id,
            name,
            email,
            join_date,
            membership_type
        FROM members
        WHERE country = %s AND active = TRUE
        ORDER BY join_date DESC
    """
    
    members = pd.read_sql(query, conn, params=(country,))
    conn.close()
    return members

def update_member_status(member_id, active):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE members
            SET active = %s
            WHERE id = %s
        """, (active, member_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
