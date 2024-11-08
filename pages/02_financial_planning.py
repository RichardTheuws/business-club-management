import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.calculations import (
    calculate_revenue_forecast,
    calculate_expenses_forecast,
    calculate_cashflow
)

def financial_planning():
    st.title("Financial Planning")
    
    # Financial Parameters
    st.subheader("Financial Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        annual_fee = st.number_input("Annual Membership Fee (€)", value=795)
        event_fee = st.number_input("Event Fee per Member (€)", value=50)
        marketing_percentage = st.slider("Marketing Budget (%)", 0, 100, 15)
    
    with col2:
        num_events = st.number_input("Number of Events per Year", value=4)
        base_salary = st.number_input("Base Salary per Employee (€)", value=5000)
        num_employees = st.number_input("Number of Employees", value=1)
    
    # Revenue Forecast
    st.subheader("Revenue Forecast")
    revenue_forecast = calculate_revenue_forecast(annual_fee, event_fee, num_events)
    fig = px.line(revenue_forecast, title="Revenue Forecast")
    st.plotly_chart(fig)
    
    # Expense Breakdown
    st.subheader("Expense Breakdown")
    expenses = calculate_expenses_forecast(
        marketing_percentage,
        base_salary,
        num_employees,
        num_events,
        event_fee
    )
    
    fig = go.Figure(data=[
        go.Pie(labels=list(expenses.keys()), values=list(expenses.values()))
    ])
    st.plotly_chart(fig)
    
    # Cash Flow Analysis
    st.subheader("Cash Flow Analysis")
    cashflow = calculate_cashflow(revenue_forecast, expenses)
    fig = px.line(cashflow, title="Cash Flow Projection")
    st.plotly_chart(fig)
    
    # Financial Alerts
    if cashflow['balance'].min() < 0:
        st.warning("⚠️ Projected negative cash flow detected!")
    
    if expenses['total'] > revenue_forecast['total'].max():
        st.warning("⚠️ Expenses exceed maximum projected revenue!")

if __name__ == "__main__":
    financial_planning()
