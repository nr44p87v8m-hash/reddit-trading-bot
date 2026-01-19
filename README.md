# 🤖 Multi-Asset Trading Bot for Reddit

Automated Reddit bot that analyzes trading symbols using the Multi-Asset Adaptive Strategy and provides real-time signals with win rate statistics.

## Features

- ✅ Analyzes 15+ assets (Gold, Silver, BTC, ETH, stocks)
- ✅ Backtests last 100 trades for win rate
- ✅ Provides current signals (LONG/SHORT/WAIT with confidence 50%/70%/90%)
- ✅ Calculates Stop Loss & Take Profit levels
- ✅ Uses Claude AI for natural language analysis
- ✅ Rate-limited (20 replies/hour)

## Setup

### 1. Get API Keys

**Reddit API:**
1. Go to https://www.reddit.com/prefs/apps
2. Create app (script type)
3. Copy `client_id` and `client_secret`

**Anthropic API:**
1. Go to https://console.anthropic.com/
2. Get your API key ($5 free credit)

### 2. Configure Secrets in Replit

Add these Secrets in Replit:
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USERNAME`
- `REDDIT_PASSWORD`
- `ANTHROPIC_API_KEY`
- `SUBREDDIT` (e.g., "test" for testing)

### 3. Run

Click "Run" button in Replit!

## Usage

In any Reddit comment, mention:
```
!analyze BTCUSD
!check GOLD
!signal SPY
```

Bot will reply with:
- Current signal (BUY/SELL/WAIT)
- Win rate from last 100 trades
- Stop Loss & Take Profit levels
- Market context analysis

## Example Response
```
## 📊 BTCUSD Analysis

🟢 Current Signal: LONG 70%

Strategy Performance:
- Win Rate: 67.5%
- Total Trades: 87 (58W / 29L)
- Profit Factor: 2.1

Trade Setup:
- Entry: $42,350
- Stop Loss: $41,200
- Take Profit: $44,650

Market showing strong bullish momentum with volume confirmation. 
ADX above 25 indicates trending conditions. Consider entry on pullback.

---
Not financial advice | Multi-Asset Adaptive Strategy
```

## Supported Symbols

Gold (XAUUSD, GOLD), Silver (XAGUSD, SILVER), Bitcoin (BTC, BTCUSD), 
Ethereum (ETH, ETHUSD), SPY, QQQ, AAPL, TSLA, NVDA, and more!

## License

MIT License - Use at your own risk. Not financial advice.