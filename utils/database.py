import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host=os.environ['PGHOST'],
        database=os.environ['PGDATABASE'],
        user=os.environ['PGUSER'],
        password=os.environ['PGPASSWORD'],
        port=os.environ['PGPORT']
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create members table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            country VARCHAR(50) NOT NULL,
            join_date DATE NOT NULL,
            membership_type VARCHAR(20) NOT NULL,
            active BOOLEAN DEFAULT TRUE
        );
    """)
    
    # Create transactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            member_id INTEGER REFERENCES members(id),
            amount DECIMAL(10,2) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            transaction_date DATE NOT NULL
        );
    """)
    
    # Create events table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            date DATE NOT NULL,
            country VARCHAR(50) NOT NULL,
            revenue DECIMAL(10,2) NOT NULL,
            costs DECIMAL(10,2) NOT NULL
        );
    """)
    
    conn.commit()
    cur.close()
    conn.close()

def get_sqlalchemy_engine():
    return create_engine(os.environ['DATABASE_URL'])

def get_session():
    engine = get_sqlalchemy_engine()
    Session = sessionmaker(bind=engine)
    return Session()
