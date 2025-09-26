# Trading settings - Dynamic for PocketOption
TRADING_SETTINGS = {
    'timeframes': ['1m', '2m', '3m', '5m'],  # PocketOption common timeframes
    'assets': [],  # Will be populated dynamically from PocketOption API
    'max_concurrent_trades': 3,
    'risk_per_trade': 2.0,  # 2% of account per trade
    'stop_loss_pips': 20,
    'take_profit_pips': 40
}

# Strategy settings
STRATEGY_SETTINGS = {
    'trend_reversal': {
        'timeframe': '5m',
        'enabled': True,
        'min_confidence': 70
    },
    'trend_following': {
        'timeframes': ['1m', '2m', '3m'],
        'enabled': True,
        'min_confidence': 65
    }
}

# PocketOption specific settings
POCKET_OPTION_CONFIG = {
    'api_endpoints': {
        'instruments': 'https://pocketoption.com/api/instruments',  # Endpoint to get available assets
        'categories': 'https://pocketoption.com/api/categories'     # Endpoint to get asset categories
    },
    'preferred_categories': ['forex', 'crypto', 'indices', 'stocks'],  # Priority order for asset types
    'trading_hours': {
        'forex': '24/5',
        'crypto': '24/7',
        'indices': 'market_hours',
        'stocks': 'market_hours'
    }
}

def get_default_assets():
    """Return a basic set of popular assets if dynamic loading fails"""
    return [
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 
        'USDCAD', 'USDCHF', 'XAUUSD', 'XAGUSD',
        'BTC', 'ETH', 'LTC', 'XRP',
        'US500', 'US30', 'NAS100', 'JP225'
    ]

async def load_available_assets():
    """
    Load available trading instruments from PocketOption API
    This should be called after successful authentication
    """
    # This function will be implemented in the WebSocket client
    # after we receive the instruments list from PocketOption
    pass
