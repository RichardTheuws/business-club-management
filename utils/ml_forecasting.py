import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from utils.database import get_db_connection
from utils.config import load_config

def prepare_time_series_data(data, feature_columns, target_column, lookback=3):
    """Prepare time series data for ML model"""
    X, y = [], []
    for i in range(len(data) - lookback):
        feature_sequence = data[feature_columns].iloc[i:(i + lookback)].values.flatten()
        target_value = data[target_column].iloc[i + lookback]
        X.append(feature_sequence)
        y.append(target_value)
    return np.array(X), np.array(y)

def predict_member_growth(historical_data=None, forecast_months=12):
    """Predict member growth using ML model"""
    try:
        if historical_data is None:
            conn = get_db_connection()
            query = """
                SELECT 
                    DATE_TRUNC('month', join_date) as month,
                    country,
                    COUNT(*) as new_members,
                    COUNT(*) FILTER (WHERE active = TRUE) as active_members
                FROM members
                GROUP BY DATE_TRUNC('month', join_date), country
                ORDER BY month
            """
            historical_data = pd.read_sql(query, conn)
            conn.close()

        # Prepare features
        historical_data['month_num'] = pd.to_datetime(historical_data['month']).dt.month
        historical_data['year'] = pd.to_datetime(historical_data['month']).dt.year
        
        feature_columns = ['month_num', 'year', 'new_members']
        lookback = 3
        
        predictions = {}
        for country in ['Netherlands', 'Belgium', 'Germany']:
            country_data = historical_data[historical_data['country'] == country].copy()
            if len(country_data) < lookback + 1:
                continue
                
            X, y = prepare_time_series_data(country_data, feature_columns, 'active_members', lookback)
            
            if len(X) == 0:
                continue
                
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Prepare forecast data
            last_date = pd.to_datetime(country_data['month'].max())
            future_dates = pd.date_range(start=last_date + timedelta(days=32),
                                       periods=forecast_months,
                                       freq='M')
            
            future_features = []
            latest_features = X[-1].reshape(-1, len(feature_columns))
            
            for date in future_dates:
                new_features = np.array([date.month, date.year, latest_features[-1][2]])
                future_features.append(new_features)
                latest_features = np.vstack([latest_features[1:], new_features])
            
            future_features = np.array(future_features)
            predictions[country] = model.predict(future_features)
            
        return predictions, future_dates
    except Exception as e:
        print(f"Error in member growth prediction: {str(e)}")
        return None, None

def predict_churn_probability(member_data=None):
    """Predict churn probability for members"""
    try:
        if member_data is None:
            conn = get_db_connection()
            query = """
                SELECT 
                    m.id,
                    m.join_date,
                    COUNT(t.id) as transaction_count,
                    AVG(t.amount) as avg_transaction,
                    m.active
                FROM members m
                LEFT JOIN transactions t ON m.id = t.member_id
                GROUP BY m.id
            """
            member_data = pd.read_sql(query, conn)
            conn.close()
        
        # Feature engineering
        member_data['membership_duration'] = (datetime.now() - 
            pd.to_datetime(member_data['join_date'])).dt.days
        
        # Prepare features
        features = ['membership_duration', 'transaction_count', 'avg_transaction']
        X = member_data[features].fillna(0)
        y = member_data['active']
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        # Calculate feature importance
        feature_importance = dict(zip(features, model.feature_importances_))
        
        # Predict probabilities
        churn_probabilities = 1 - model.predict(X_scaled)
        
        return pd.DataFrame({
            'member_id': member_data['id'],
            'churn_probability': churn_probabilities,
            'feature_importance': [feature_importance] * len(churn_probabilities)
        })
    except Exception as e:
        print(f"Error in churn prediction: {str(e)}")
        return None

def predict_revenue(historical_data=None, forecast_months=12):
    """Predict future revenue using ML model"""
    try:
        if historical_data is None:
            conn = get_db_connection()
            query = """
                SELECT 
                    DATE_TRUNC('month', transaction_date) as month,
                    SUM(amount) as revenue,
                    COUNT(DISTINCT member_id) as active_members,
                    COUNT(*) as transaction_count
                FROM transactions
                GROUP BY DATE_TRUNC('month', transaction_date)
                ORDER BY month
            """
            historical_data = pd.read_sql(query, conn)
            conn.close()
        
        # Prepare features
        historical_data['month_num'] = pd.to_datetime(historical_data['month']).dt.month
        historical_data['year'] = pd.to_datetime(historical_data['month']).dt.year
        
        feature_columns = ['month_num', 'year', 'active_members', 'transaction_count']
        target_column = 'revenue'
        lookback = 3
        
        X, y = prepare_time_series_data(historical_data, feature_columns, target_column, lookback)
        
        if len(X) == 0:
            return None, None
            
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Prepare forecast data
        last_date = pd.to_datetime(historical_data['month'].max())
        future_dates = pd.date_range(start=last_date + timedelta(days=32),
                                   periods=forecast_months,
                                   freq='M')
        
        future_features = []
        latest_features = X[-1].reshape(-1, len(feature_columns))
        
        for date in future_dates:
            new_features = np.array([
                date.month,
                date.year,
                latest_features[-1][2],  # Use last active_members
                latest_features[-1][3]   # Use last transaction_count
            ])
            future_features.append(new_features)
            latest_features = np.vstack([latest_features[1:], new_features])
        
        future_features = np.array(future_features)
        predictions = model.predict(future_features)
        
        return predictions, future_dates
    except Exception as e:
        print(f"Error in revenue prediction: {str(e)}")
        return None, None
