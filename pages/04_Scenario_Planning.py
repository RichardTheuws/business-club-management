import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.calculations import (
    calculate_revenue_forecast,
    calculate_expenses_forecast,
    calculate_cashflow
)
from utils.ml_forecasting import (
    predict_member_growth,
    predict_churn_probability,
    predict_revenue
)
from utils.config import load_config
from utils.database import init_db
import pandas as pd

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
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Traditional Forecasting",
        "ML Growth Predictions",
        "Churn Analysis",
        "ML Revenue Forecast"
    ])
    
    with tab1:
        st.subheader("Traditional Scenario Analysis")
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
                    marketing_percentage, 5000, 1,
                    num_events, event_fee, scenario
                )
                cashflows[scenario] = calculate_cashflow(
                    forecasts[scenario], expenses[scenario], scenario
                )
            
            # Display traditional forecasts
            st.subheader("Member Growth Projections")
            fig = go.Figure()
            
            for scenario in scenarios:
                fig.add_trace(go.Scatter(
                    x=forecasts[scenario].index,
                    y=forecasts[scenario]['total_members'],
                    name=f"{scenario.title()} Scenario",
                    mode='lines+markers'
                ))
            
            fig.update_layout(
                title="Traditional Growth Forecast",
                xaxis_title="Month",
                yaxis_title="Number of Members"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error in traditional forecasting: {str(e)}")
    
    with tab2:
        st.subheader("ML-Based Growth Predictions")
        try:
            predictions, future_dates = predict_member_growth()
            
            if predictions and future_dates is not None:
                fig = go.Figure()
                
                for country, pred in predictions.items():
                    fig.add_trace(go.Scatter(
                        x=future_dates,
                        y=pred,
                        name=f"{country} ML Prediction",
                        mode='lines+markers'
                    ))
                
                fig.update_layout(
                    title="ML-Based Member Growth Forecast",
                    xaxis_title="Month",
                    yaxis_title="Predicted Members"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparison with traditional forecast
                st.subheader("ML vs Traditional Forecast Comparison")
                realistic_forecast = forecasts['realistic']
                
                fig = go.Figure()
                
                # Add ML predictions
                total_ml_prediction = sum(pred for pred in predictions.values())
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=total_ml_prediction,
                    name="ML Prediction",
                    mode='lines+markers'
                ))
                
                # Add traditional forecast
                fig.add_trace(go.Scatter(
                    x=realistic_forecast.index,
                    y=realistic_forecast['total_members'],
                    name="Traditional Forecast",
                    mode='lines+markers'
                ))
                
                fig.update_layout(
                    title="ML vs Traditional Growth Comparison",
                    xaxis_title="Month",
                    yaxis_title="Number of Members"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for ML predictions. Please accumulate more historical data.")
                
        except Exception as e:
            st.error(f"Error in ML growth predictions: {str(e)}")
    
    with tab3:
        st.subheader("Churn Risk Analysis")
        try:
            churn_predictions = predict_churn_probability()
            
            if churn_predictions is not None:
                # Display high-risk members
                high_risk = churn_predictions[churn_predictions['churn_probability'] > 0.7]
                
                st.write("High Risk Members (>70% churn probability)")
                if not high_risk.empty:
                    st.dataframe(high_risk)
                else:
                    st.write("No high-risk members identified")
                
                # Churn probability distribution
                fig = px.histogram(
                    churn_predictions,
                    x='churn_probability',
                    nbins=20,
                    title="Churn Probability Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Feature importance visualization
                if len(churn_predictions) > 0:
                    feature_importance = churn_predictions['feature_importance'].iloc[0]
                    importance_df = pd.DataFrame({
                        'Feature': feature_importance.keys(),
                        'Importance': feature_importance.values()
                    })
                    
                    fig = px.bar(
                        importance_df,
                        x='Feature',
                        y='Importance',
                        title="Churn Prediction Feature Importance"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient data for churn predictions. Please accumulate more historical data.")
                
        except Exception as e:
            st.error(f"Error in churn analysis: {str(e)}")
    
    with tab4:
        st.subheader("ML-Based Revenue Forecast")
        try:
            revenue_predictions, future_dates = predict_revenue()
            
            if revenue_predictions is not None and future_dates is not None:
                # Create revenue forecast visualization
                fig = go.Figure()
                
                # Add ML prediction
                fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=revenue_predictions,
                    name="ML Revenue Prediction",
                    mode='lines+markers'
                ))
                
                # Add traditional forecast for comparison
                realistic_forecast = forecasts['realistic']
                fig.add_trace(go.Scatter(
                    x=realistic_forecast.index,
                    y=realistic_forecast['total_revenue'],
                    name="Traditional Revenue Forecast",
                    mode='lines+markers'
                ))
                
                fig.update_layout(
                    title="Revenue Forecast Comparison",
                    xaxis_title="Month",
                    yaxis_title="Revenue (€)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Calculate and display forecast differences
                ml_total = sum(revenue_predictions)
                traditional_total = sum(realistic_forecast['total_revenue'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("ML Forecast Total", f"€{ml_total:,.2f}")
                with col2:
                    st.metric("Traditional Forecast Total", f"€{traditional_total:,.2f}")
                with col3:
                    difference = ((ml_total - traditional_total) / traditional_total) * 100
                    st.metric("Forecast Difference", f"{difference:,.1f}%")
            else:
                st.warning("Insufficient data for ML revenue predictions. Please accumulate more historical data.")
                
        except Exception as e:
            st.error(f"Error in ML revenue forecast: {str(e)}")

if __name__ == "__main__":
    scenario_planning()