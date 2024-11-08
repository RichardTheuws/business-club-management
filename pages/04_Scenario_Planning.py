import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.calculations import (
    calculate_revenue_forecast,
    calculate_expenses_forecast,
    calculate_cashflow
)
from utils.config import load_config
from utils.database import init_db

def scenario_planning():
    st.title("Scenario Planning")
    
    # Initialize database if needed
    init_db()
    
    # Load configuration
    config = load_config()
    
    # Sidebar controls
    st.sidebar.header("Scenario Parameters")
    
    # Basic parameters
    annual_fee = st.sidebar.number_input("Annual Membership Fee (€)", value=config['annual_fee'])
    event_fee = st.sidebar.number_input("Event Fee per Member (€)", value=config['event_fee'])
    num_events = st.sidebar.number_input("Number of Events per Year", value=config['num_events'])
    marketing_percentage = st.sidebar.slider("Marketing Budget (%)", 0, 100, config['marketing_percentage'])
    
    # Growth rate adjustments
    st.sidebar.subheader("Growth Rate Adjustments")
    nl_growth = st.sidebar.number_input("Netherlands Monthly Growth (%)", 
                                      value=config['growth_targets']['Netherlands'])
    be_growth = st.sidebar.number_input("Belgium Monthly Growth (%)", 
                                      value=config['growth_targets']['Belgium'])
    de_growth = st.sidebar.number_input("Germany Monthly New Members", 
                                      value=config['growth_targets']['Germany'])
    
    # Update config with new values
    growth_config = config.copy()
    growth_config['growth_targets']['Netherlands'] = nl_growth
    growth_config['growth_targets']['Belgium'] = be_growth
    growth_config['growth_targets']['Germany'] = de_growth
    
    # Main content
    scenarios = ['pessimistic', 'realistic', 'optimistic']
    
    try:
        # Initialize forecast data for all scenarios
        forecasts = {}
        expenses = {}
        cashflows = {}
        
        for scenario in scenarios:
            forecasts[scenario] = calculate_revenue_forecast(
                annual_fee, event_fee, num_events, scenario
            )
            expenses[scenario] = calculate_expenses_forecast(
                marketing_percentage, 5000, 1,  # Base salary of 5000
                num_events, event_fee, scenario
            )
            cashflows[scenario] = calculate_cashflow(
                forecasts[scenario], expenses[scenario], scenario
            )
        
        # Visualization tabs
        tab1, tab2, tab3 = st.tabs(["Member Growth", "Revenue Forecast", "Cash Flow"])
        
        with tab1:
            st.subheader("Projected Member Growth by Scenario")
            fig = go.Figure()
            
            for scenario in scenarios:
                fig.add_trace(go.Scatter(
                    x=forecasts[scenario].index,
                    y=forecasts[scenario]['total_members'],
                    name=f"{scenario.title()} Scenario",
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Total Members Projection",
                xaxis_title="Month",
                yaxis_title="Number of Members"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Country-wise breakdown
            st.subheader("Member Growth by Country")
            selected_scenario = st.selectbox(
                "Select Scenario for Country Breakdown",
                scenarios,
                index=scenarios.index('realistic')
            )
            
            fig = go.Figure()
            for country in ['Netherlands', 'Belgium', 'Germany']:
                fig.add_trace(go.Scatter(
                    x=forecasts[selected_scenario].index,
                    y=forecasts[selected_scenario][f'{country}_members'],
                    name=country,
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title=f"Member Growth by Country ({selected_scenario.title()} Scenario)",
                xaxis_title="Month",
                yaxis_title="Number of Members"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Revenue Forecast by Scenario")
            fig = go.Figure()
            
            for scenario in scenarios:
                fig.add_trace(go.Scatter(
                    x=forecasts[scenario].index,
                    y=forecasts[scenario]['total_revenue'],
                    name=f"{scenario.title()} Scenario",
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Monthly Revenue Projection",
                xaxis_title="Month",
                yaxis_title="Revenue (€)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Revenue breakdown
            st.subheader("Revenue Breakdown")
            selected_scenario = st.selectbox(
                "Select Scenario for Revenue Breakdown",
                scenarios,
                index=scenarios.index('realistic'),
                key="revenue_scenario"
            )
            
            fig = go.Figure()
            for revenue_type in ['membership_revenue', 'event_revenue']:
                fig.add_trace(go.Bar(
                    x=forecasts[selected_scenario].index,
                    y=forecasts[selected_scenario][revenue_type],
                    name=revenue_type.replace('_', ' ').title()
                ))
            
            fig.update_layout(
                title=f"Revenue Breakdown ({selected_scenario.title()} Scenario)",
                xaxis_title="Month",
                yaxis_title="Revenue (€)",
                barmode='stack'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("Cash Flow Analysis by Scenario")
            fig = go.Figure()
            
            for scenario in scenarios:
                fig.add_trace(go.Scatter(
                    x=cashflows[scenario].index,
                    y=cashflows[scenario]['cumulative_cashflow'],
                    name=f"{scenario.title()} Scenario",
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Cumulative Cash Flow Projection",
                xaxis_title="Month",
                yaxis_title="Cumulative Cash Flow (€)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly cash flow details
            st.subheader("Monthly Cash Flow Details")
            selected_scenario = st.selectbox(
                "Select Scenario for Cash Flow Details",
                scenarios,
                index=scenarios.index('realistic'),
                key="cashflow_scenario"
            )
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=cashflows[selected_scenario].index,
                y=cashflows[selected_scenario]['total_revenue'],
                name='Revenue'
            ))
            fig.add_trace(go.Bar(
                x=cashflows[selected_scenario].index,
                y=-cashflows[selected_scenario]['expenses'],
                name='Expenses'
            ))
            fig.add_trace(go.Scatter(
                x=cashflows[selected_scenario].index,
                y=cashflows[selected_scenario]['net_cashflow'],
                name='Net Cash Flow',
                mode='lines+markers'
            ))
            
            fig.update_layout(
                title=f"Monthly Cash Flow Details ({selected_scenario.title()} Scenario)",
                xaxis_title="Month",
                yaxis_title="Amount (€)",
                barmode='relative'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"An error occurred while generating the scenarios: {str(e)}")

if __name__ == "__main__":
    scenario_planning()
