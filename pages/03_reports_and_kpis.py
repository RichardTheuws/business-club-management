import streamlit as st
import plotly.express as px
from utils.calculations import (
    calculate_member_kpis,
    calculate_financial_kpis,
    calculate_event_metrics
)

def reports_and_kpis():
    st.title("Reports & KPIs")
    
    # Time Period Selection
    period = st.selectbox("Select Time Period", 
                         ["Last Month", "Last Quarter", "Last Year", "All Time"])
    
    # KPI Dashboard
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    member_kpis = calculate_member_kpis(period)
    financial_kpis = calculate_financial_kpis(period)
    
    with col1:
        st.metric("Member Growth Rate", 
                 f"{member_kpis['growth_rate']}%",
                 delta=member_kpis['growth_rate_change'])
        
    with col2:
        st.metric("Retention Rate", 
                 f"{member_kpis['retention_rate']}%",
                 delta=member_kpis['retention_rate_change'])
        
    with col3:
        st.metric("Revenue per Member", 
                 f"€{financial_kpis['revenue_per_member']:,.2f}",
                 delta=financial_kpis['revenue_per_member_change'])
        
    with col4:
        st.metric("Operating Margin", 
                 f"{financial_kpis['operating_margin']}%",
                 delta=financial_kpis['operating_margin_change'])
    
    # Detailed Reports
    tab1, tab2, tab3 = st.tabs(["Member Analytics", "Financial Metrics", "Event Performance"])
    
    with tab1:
        # Member Growth Chart
        growth_data = member_kpis['growth_data']
        fig = px.line(growth_data, title="Member Growth Over Time")
        st.plotly_chart(fig)
        
        # Member Distribution
        dist_data = member_kpis['distribution_data']
        fig = px.pie(dist_data, title="Member Distribution by Country")
        st.plotly_chart(fig)
    
    with tab2:
        # Revenue vs Expenses
        fin_data = financial_kpis['financial_data']
        fig = px.bar(fin_data, title="Revenue vs Expenses")
        st.plotly_chart(fig)
        
        # Cash Flow Trend
        cash_data = financial_kpis['cash_flow_data']
        fig = px.line(cash_data, title="Cash Flow Trend")
        st.plotly_chart(fig)
    
    with tab3:
        event_metrics = calculate_event_metrics(period)
        
        # Event Attendance
        fig = px.bar(event_metrics['attendance_data'], 
                    title="Event Attendance")
        st.plotly_chart(fig)
        
        # Event Revenue
        fig = px.line(event_metrics['revenue_data'], 
                     title="Event Revenue")
        st.plotly_chart(fig)

if __name__ == "__main__":
    reports_and_kpis()
