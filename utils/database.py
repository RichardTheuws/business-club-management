import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import re

def get_sqlalchemy_engine():
    return create_engine(os.environ['DATABASE_URL'])

def get_session():
    engine = get_sqlalchemy_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_db():
    engine = get_sqlalchemy_engine()
    
    # Create tables
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS members (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                country VARCHAR(50) NOT NULL,
                join_date DATE NOT NULL,
                membership_type VARCHAR(20) NOT NULL,
                active BOOLEAN DEFAULT TRUE
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                member_id INTEGER REFERENCES members(id),
                amount DECIMAL(10,2) NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                transaction_date DATE NOT NULL
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                date DATE NOT NULL,
                country VARCHAR(50) NOT NULL,
                revenue DECIMAL(10,2) NOT NULL,
                costs DECIMAL(10,2) NOT NULL
            )
        """))
        conn.commit()

def validate_import_data(table_name, data):
    """Validate imported data before insertion"""
    if data.empty:
        return False, "No data provided"
    
    if table_name == 'members':
        required_columns = ['name', 'email', 'country', 'join_date', 'membership_type']
        if not all(col in data.columns for col in required_columns):
            return False, f"Missing required columns. Required: {', '.join(required_columns)}"
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_emails = data[~data['email'].str.match(email_pattern)]['email'].tolist()
        if invalid_emails:
            return False, f"Invalid email format: {', '.join(invalid_emails)}"
        
        # Validate country
        valid_countries = ['Netherlands', 'Belgium', 'Germany']
        invalid_countries = data[~data['country'].isin(valid_countries)]['country'].unique()
        if len(invalid_countries) > 0:
            return False, f"Invalid countries: {', '.join(invalid_countries)}"
        
        # Validate membership type
        valid_types = ['Standard', 'Premium']
        invalid_types = data[~data['membership_type'].isin(valid_types)]['membership_type'].unique()
        if len(invalid_types) > 0:
            return False, f"Invalid membership types: {', '.join(invalid_types)}"
    
    elif table_name == 'transactions':
        required_columns = ['member_email', 'amount', 'transaction_type', 'transaction_date']
        if not all(col in data.columns for col in required_columns):
            return False, f"Missing required columns. Required: {', '.join(required_columns)}"
        
        # Validate transaction types
        valid_types = ['membership_fee', 'event_fee']
        invalid_types = data[~data['transaction_type'].isin(valid_types)]['transaction_type'].unique()
        if len(invalid_types) > 0:
            return False, f"Invalid transaction types: {', '.join(invalid_types)}"
        
        # Validate amounts
        if (data['amount'] <= 0).any():
            return False, "All amounts must be positive"
    
    elif table_name == 'events':
        required_columns = ['name', 'date', 'country', 'revenue', 'costs']
        if not all(col in data.columns for col in required_columns):
            return False, f"Missing required columns. Required: {', '.join(required_columns)}"
        
        # Validate country
        valid_countries = ['Netherlands', 'Belgium', 'Germany']
        invalid_countries = data[~data['country'].isin(valid_countries)]['country'].unique()
        if len(invalid_countries) > 0:
            return False, f"Invalid countries: {', '.join(invalid_countries)}"
        
        # Validate amounts
        if (data['revenue'] < 0).any() or (data['costs'] < 0).any():
            return False, "Revenue and costs must not be negative"
    
    return True, "Data validation passed"

def bulk_import_data(table_name, data):
    """Import data in bulk with proper error handling"""
    engine = get_sqlalchemy_engine()
    
    try:
        if table_name == 'members':
            data['join_date'] = pd.to_datetime(data['join_date']).dt.date
            if 'active' not in data.columns:
                data['active'] = True
            data.to_sql('members', engine, if_exists='append', index=False)
        
        elif table_name == 'transactions':
            # Get member IDs from emails
            with engine.connect() as conn:
                member_query = text("""
                    SELECT id, email FROM members
                    WHERE email IN :emails
                """)
                member_results = conn.execute(
                    member_query,
                    {"emails": tuple(data['member_email'].unique())}
                ).fetchall()
                
                member_ids = {row[1]: row[0] for row in member_results}
            
            # Replace email with member_id
            data['member_id'] = data['member_email'].map(member_ids)
            data['transaction_date'] = pd.to_datetime(data['transaction_date']).dt.date
            
            # Drop email column and import
            data = data.drop('member_email', axis=1)
            data = data[~data['member_id'].isna()]  # Remove rows with invalid member emails
            data.to_sql('transactions', engine, if_exists='append', index=False)
        
        elif table_name == 'events':
            data['date'] = pd.to_datetime(data['date']).dt.date
            data.to_sql('events', engine, if_exists='append', index=False)
        
        return True
    
    except SQLAlchemyError as e:
        print(f"Error importing data: {str(e)}")
        return False

def verify_data_consistency():
    """Check for data consistency issues"""
    engine = get_sqlalchemy_engine()
    issues = []
    
    try:
        with engine.connect() as conn:
            # Check for transactions without valid members
            orphan_transactions = conn.execute(text("""
                SELECT COUNT(*) FROM transactions t
                LEFT JOIN members m ON t.member_id = m.id
                WHERE m.id IS NULL
            """)).scalar()
            
            if orphan_transactions > 0:
                issues.append(f"Found {orphan_transactions} transactions with invalid member references")
            
            # Check for membership fee consistency
            incorrect_fees = conn.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE transaction_type = 'membership_fee'
                AND amount != 795.00
            """)).scalar()
            
            if incorrect_fees > 0:
                issues.append(f"Found {incorrect_fees} membership fee transactions with incorrect amounts")
            
            # Check for duplicate member emails
            duplicate_emails = conn.execute(text("""
                SELECT email, COUNT(*) as count
                FROM members
                GROUP BY email
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_emails:
                issues.append(f"Found duplicate member emails: {', '.join(row[0] for row in duplicate_emails)}")
            
            # Check for future dates
            future_members = conn.execute(text("""
                SELECT COUNT(*) FROM members
                WHERE join_date > CURRENT_DATE
            """)).scalar()
            
            if future_members > 0:
                issues.append(f"Found {future_members} members with future join dates")
            
            future_transactions = conn.execute(text("""
                SELECT COUNT(*) FROM transactions
                WHERE transaction_date > CURRENT_DATE
            """)).scalar()
            
            if future_transactions > 0:
                issues.append(f"Found {future_transactions} transactions with future dates")
        
        return issues
    
    except SQLAlchemyError as e:
        print(f"Error checking data consistency: {str(e)}")
        return ["Error performing consistency checks"]

def get_data_templates(template_type):
    """Get example templates for data import"""
    if template_type == 'members':
        return pd.DataFrame({
            'name': ['John Doe', 'Jane Smith'],
            'email': ['john@example.com', 'jane@example.com'],
            'country': ['Netherlands', 'Belgium'],
            'join_date': ['2024-01-01', '2024-01-02'],
            'membership_type': ['Standard', 'Premium'],
            'active': [True, True]
        })
    
    elif template_type == 'transactions':
        return pd.DataFrame({
            'member_email': ['john@example.com', 'jane@example.com'],
            'amount': [795.00, 50.00],
            'transaction_type': ['membership_fee', 'event_fee'],
            'transaction_date': ['2024-01-01', '2024-01-02']
        })
    
    elif template_type == 'events':
        return pd.DataFrame({
            'name': ['Networking Event', 'Workshop'],
            'date': ['2024-01-15', '2024-02-01'],
            'country': ['Netherlands', 'Belgium'],
            'revenue': [2500.00, 1800.00],
            'costs': [1000.00, 800.00]
        })
    
    return pd.DataFrame()

def get_db_data(query, params=None):
    """Unified function to get data from database using SQLAlchemy"""
    try:
        engine = get_sqlalchemy_engine()
        with engine.connect() as conn:
            if params:
                result = pd.read_sql(text(query), conn, params=params)
            else:
                result = pd.read_sql(text(query), conn)
        return result
    except SQLAlchemyError as e:
        print(f"Database error: {str(e)}")
        return pd.DataFrame()

def seed_sample_data():
    """Generate and insert sample historical data for ML training"""
    engine = get_sqlalchemy_engine()
    
    try:
        # Generate sample member data
        countries = ['Netherlands', 'Belgium', 'Germany']
        membership_types = ['Standard', 'Premium']
        start_date = datetime.now() - timedelta(days=365)
        
        # Generate member data
        members_data = []
        email_counter = 1
        
        for country in countries:
            num_members = np.random.randint(50, 200)
            for _ in range(num_members):
                join_date = start_date + timedelta(days=np.random.randint(0, 365))
                active = np.random.choice([True, True, True, False])  # 75% active rate
                members_data.append({
                    'name': f'Member {email_counter}',
                    'email': f'member{email_counter}@example.com',
                    'country': country,
                    'join_date': join_date,
                    'membership_type': np.random.choice(membership_types),
                    'active': active
                })
                email_counter += 1
        
        # Insert member data
        members_df = pd.DataFrame(members_data)
        members_df.to_sql('members', engine, if_exists='append', index=False)
        
        # Get member IDs for transactions
        with engine.connect() as conn:
            member_ids = pd.read_sql("SELECT id FROM members", conn)['id'].tolist()
        
        # Generate transaction data
        transactions_data = []
        for member_id in member_ids:
            num_transactions = np.random.randint(3, 12)
            for _ in range(num_transactions):
                transaction_date = start_date + timedelta(days=np.random.randint(0, 365))
                transaction_type = np.random.choice(['membership_fee', 'event_fee'])
                amount = 795.0 if transaction_type == 'membership_fee' else 50.0
                transactions_data.append({
                    'member_id': member_id,
                    'amount': amount,
                    'transaction_type': transaction_type,
                    'transaction_date': transaction_date
                })
        
        # Insert transaction data
        transactions_df = pd.DataFrame(transactions_data)
        transactions_df.to_sql('transactions', engine, if_exists='append', index=False)
        
        # Generate event data
        events_data = []
        for country in countries:
            num_events = np.random.randint(4, 8)
            for i in range(num_events):
                event_date = start_date + timedelta(days=np.random.randint(0, 365))
                num_attendees = np.random.randint(20, 100)
                revenue = num_attendees * 50.0
                costs = revenue * np.random.uniform(0.4, 0.6)
                events_data.append({
                    'name': f'{country} Event {i+1}',
                    'date': event_date,
                    'country': country,
                    'revenue': revenue,
                    'costs': costs
                })
        
        # Insert event data
        events_df = pd.DataFrame(events_data)
        events_df.to_sql('events', engine, if_exists='append', index=False)
        
        return True
        
    except SQLAlchemyError as e:
        print(f"Error seeding sample data: {str(e)}")
        return False
