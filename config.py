import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API Configuration
REDDIT_CONFIG = {
    'client_id': os.getenv('REDDIT_CLIENT_ID', 'YOUR_CLIENT_ID'),
    'client_secret': os.getenv('REDDIT_CLIENT_SECRET', 'YOUR_CLIENT_SECRET'),
    'user_agent': 'Multi-Asset Trading Bot v1.0 by /u/YOUR_USERNAME',
    'username': os.getenv('REDDIT_USERNAME', 'YOUR_BOT_USERNAME'),
    'password': os.getenv('REDDIT_PASSWORD', 'YOUR_BOT_PASSWORD')
}

# Claude API
CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'YOUR_ANTHROPIC_KEY')

# Bot Settings
SUBREDDIT_NAME = os.getenv('SUBREDDIT', 'test')  
CHECK_INTERVAL = 30  
MAX_REPLIES_PER_HOUR = 20  

# Symbol Mapping (Reddit -> Yahoo Finance)
SYMBOL_MAP = {
    'XAUUSD': 'GC=F',      # Gold Futures
    'GOLD': 'GC=F',
    'XAU': 'GC=F',
    'XAGUSD': 'SI=F',      # Silver Futures
    'SILVER': 'SI=F',
    'XAG': 'SI=F',
    'BTCUSD': 'BTC-USD',
    'BTC': 'BTC-USD',
    'BITCOIN': 'BTC-USD',
    'ETHUSD': 'ETH-USD',
    'ETH': 'ETH-USD',
    'ETHEREUM': 'ETH-USD',
    'SPY': 'SPY',
    'QQQ': 'QQQ',
    'AAPL': 'AAPL',
    'TSLA': 'TSLA',
    'NVDA': 'NVDA',
}

# Asset Type Detection
ASSET_TYPES = {
    'BTC': 'Bitcoin',
    'BITCOIN': 'Bitcoin',
    'ETH': 'Ethereum',
    'ETHEREUM': 'Ethereum',
    'GOLD': 'Gold',
    'XAU': 'Gold',
    'SILVER': 'Silver',
    'XAG': 'Silver',
    'PALLADIUM': 'Palladium',
    'PLATINUM': 'Platinum',
}