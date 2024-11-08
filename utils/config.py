def load_config():
    """
    Load application configuration settings
    """
    return {
        'annual_fee': 795,
        'event_fee': 50,
        'num_events': 4,
        'marketing_percentage': 15,
        'monthly_expenses': 15000,  # Base monthly expenses
        'country_manager_fee': 100,  # Per member per year
        'starting_members': {
            'Netherlands': 135,
            'Belgium': 26,
            'Germany': 0
        },
        'growth_targets': {
            'Netherlands': 10,  # Percentage per month
            'Belgium': 15,
            'Germany': 63  # Absolute number per month
        }
    }
