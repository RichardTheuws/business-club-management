import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from utils.database import get_db_data
from utils.config import load_config

def validate_data_requirements(data, min_rows=6, required_columns=None):
    """Validate if data meets minimum requirements for ML training"""
    if data is None or data.empty:
        return False, "No data available"
    
    if len(data) < min_rows:
        return False, f"Insufficient data: {len(data)} rows available, minimum {min_rows} required"
    
    if required_columns:
        missing_cols = [col for col in required_columns if col not in data.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}"
    
    return True, "Data validation passed"

def get_default_predictions(forecast_months=12, trend='neutral'):
    """Generate default predictions when ML predictions are not possible"""
    config = load_config()
    base_members = {
        'Netherlands': config['starting_members']['Netherlands'],
        'Belgium': config['starting_members']['Belgium'],
        'Germany': config['starting_members']['Germany']
    }
    
    growth_rates = {
        'low': 0.02,
        'neutral': 0.05,
        'high': 0.08
    }
    
    growth_rate = growth_rates[trend]
    future_dates = pd.date_range(start=datetime.now(), periods=forecast_months, freq='M')
    
    predictions = {}
    for country in base_members:
        base = base_members[country]
        predictions[country] = np.array([base * (1 + growth_rate) ** i for i in range(forecast_months)])
    
    return predictions, future_dates

def prepare_time_series_data(data, feature_columns, target_column, lookback=3):
    """Prepare time series data for ML model with validation"""
    if len(data) <= lookback:
        return None, None, "Insufficient data for time series preparation"
    
    try:
        X, y = [], []
        for i in range(len(data) - lookback):
            feature_sequence = data[feature_columns].iloc[i:(i + lookback)].values.flatten()
            target_value = data[target_column].iloc[i + lookback]
            X.append(feature_sequence)
            y.append(target_value)
        return np.array(X), np.array(y), None
    except Exception as e:
        return None, None, f"Error preparing time series data: {str(e)}"

def predict_member_growth(historical_data=None, forecast_months=12):
    """Predict member growth using ML model with enhanced error handling"""
    try:
        if historical_data is None:
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
            historical_data = get_db_data(query)
        
        # Validate data
        valid, message = validate_data_requirements(
            historical_data,
            min_rows=6,
            required_columns=['month', 'country', 'new_members', 'active_members']
        )
        
        if not valid:
            print(f"Warning: {message}")
            return get_default_predictions(forecast_months)
        
        # Prepare features
        historical_data['month_num'] = pd.to_datetime(historical_data['month']).dt.month
        historical_data['year'] = pd.to_datetime(historical_data['month']).dt.year
        
        feature_columns = ['month_num', 'year', 'new_members']
        lookback = 3
        
        predictions = {}
        future_dates = pd.date_range(
            start=pd.to_datetime(historical_data['month'].max()) + timedelta(days=32),
            periods=forecast_months,
            freq='M'
        )
        
        for country in ['Netherlands', 'Belgium', 'Germany']:
            country_data = historical_data[historical_data['country'] == country].copy()
            
            valid, message = validate_data_requirements(country_data, min_rows=lookback + 1)
            if not valid:
                print(f"Warning for {country}: {message}")
                continue
            
            X, y, error = prepare_time_series_data(
                country_data, feature_columns, 'active_members', lookback
            )
            
            if error:
                print(f"Error for {country}: {error}")
                continue
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Prepare forecast data
            future_features = []
            latest_features = X[-1].reshape(-1, len(feature_columns))
            
            for date in future_dates:
                new_features = np.array([date.month, date.year, latest_features[-1][2]])
                future_features.append(new_features)
                latest_features = np.vstack([latest_features[1:], new_features])
            
            future_features = np.array(future_features)
            predictions[country] = model.predict(future_features)
        
        if not predictions:
            return get_default_predictions(forecast_months)
        
        return predictions, future_dates
        
    except Exception as e:
        print(f"Error in member growth prediction: {str(e)}")
        return get_default_predictions(forecast_months)

def predict_churn_probability(member_data=None):
    """Predict churn probability with enhanced error handling"""
    try:
        if member_data is None:
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
            member_data = get_db_data(query)
        
        # Validate data
        valid, message = validate_data_requirements(
            member_data,
            min_rows=10,
            required_columns=['id', 'join_date', 'transaction_count', 'avg_transaction', 'active']
        )
        
        if not valid:
            print(f"Warning: {message}")
            return None
        
        # Feature engineering
        member_data['membership_duration'] = (
            datetime.now() - pd.to_datetime(member_data['join_date'])
        ).dt.days
        
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
    """Predict future revenue with enhanced error handling"""
    try:
        if historical_data is None:
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
            historical_data = get_db_data(query)
        
        # Validate data
        valid, message = validate_data_requirements(
            historical_data,
            min_rows=6,
            required_columns=['month', 'revenue', 'active_members', 'transaction_count']
        )
        
        if not valid:
            print(f"Warning: {message}")
            default_predictions, future_dates = get_default_predictions(forecast_months)
            total_members = sum(default_predictions.values())
            config = load_config()
            return (total_members * config['annual_fee'] / 12), future_dates
        
        # Prepare features
        historical_data['month_num'] = pd.to_datetime(historical_data['month']).dt.month
        historical_data['year'] = pd.to_datetime(historical_data['month']).dt.year
        
        feature_columns = ['month_num', 'year', 'active_members', 'transaction_count']
        target_column = 'revenue'
        lookback = 3
        
        X, y, error = prepare_time_series_data(
            historical_data, feature_columns, target_column, lookback
        )
        
        if error:
            print(f"Warning: {error}")
            default_predictions, future_dates = get_default_predictions(forecast_months)
            total_members = sum(default_predictions.values())
            config = load_config()
            return (total_members * config['annual_fee'] / 12), future_dates
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Prepare forecast data
        future_dates = pd.date_range(
            start=pd.to_datetime(historical_data['month'].max()) + timedelta(days=32),
            periods=forecast_months,
            freq='M'
        )
        
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
        default_predictions, future_dates = get_default_predictions(forecast_months)
        total_members = sum(default_predictions.values())
        config = load_config()
        return (total_members * config['annual_fee'] / 12), future_dates
