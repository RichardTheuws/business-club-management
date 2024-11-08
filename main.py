import streamlit as st
import plotly.express as px
from utils.database import init_db
from utils.config import load_config
from utils.calculations import calculate_total_members, calculate_monthly_revenue

def main():
    st.set_page_config(
        page_title="Business Club Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize database
    init_db()
    
    # Load configuration
    config = load_config()
    
    st.title("Business Club Management Dashboard")
    
    # Quick Overview Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_members = calculate_total_members()
        st.metric("Total Members", total_members)
        
    with col2:
        monthly_revenue = calculate_monthly_revenue()
        st.metric("Monthly Revenue", f"€{monthly_revenue:,.2f}")
        
    with col3:
        cash_position = monthly_revenue - config['monthly_expenses']
        st.metric("Cash Position", f"€{cash_position:,.2f}")
    
    # Summary Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Member Growth Chart
        member_data = {
            'Country': ['Netherlands', 'Belgium', 'Germany'],
            'Members': [135, 26, 0]  # Initial numbers
        }
        fig = px.bar(member_data, x='Country', y='Members', title='Members by Country')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Revenue Distribution
        revenue_data = {
            'Source': ['Membership', 'Events', 'Other'],
            'Amount': [
                config['annual_fee'] * total_members / 12,
                config['event_fee'] * total_members / 3,
                0
            ]
        }
        fig = px.pie(revenue_data, values='Amount', names='Source', title='Revenue Distribution')
        st.plotly_chart(fig, use_container_width=True)
    
    # Quick Actions
    st.subheader("Quick Actions")
    cols = st.columns(4)
    with cols[0]:
        if st.button("Add New Member"):
            st.switch_page("pages/01_member_management.py")
    with cols[1]:
        if st.button("Financial Overview"):
            st.switch_page("pages/02_financial_planning.py")
    with cols[2]:
        if st.button("View Reports"):
            st.switch_page("pages/03_reports_and_kpis.py")
    with cols[3]:
        if st.button("Scenario Planning"):
            st.switch_page("pages/04_scenario_planning.py")

if __name__ == "__main__":
    main()
