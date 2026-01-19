#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import praw
import time
from datetime import datetime, timedelta
from anthropic import Anthropic
from strategy import MultiAssetStrategy
from config import *

class TradingRedditBot:
    def __init__(self):
        self.reddit = praw.Reddit(**REDDIT_CONFIG)
        self.subreddit = self.reddit.subreddit(SUBREDDIT_NAME)
        self.claude = Anthropic(api_key=CLAUDE_API_KEY)
        self.processed_comments = set()
        self.reply_count = 0
        self.last_reset = datetime.now()
        
        print(f"🤖 Bot initialized for r/{SUBREDDIT_NAME}")
        print(f"📊 Monitoring symbols: {list(SYMBOL_MAP.keys())[:5]}...")
        
    def run(self):
        """Основной цикл бота"""
        print(f"\n✅ Bot started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Monitoring comments every {CHECK_INTERVAL}s...")
        print(f"⚡ Max replies per hour: {MAX_REPLIES_PER_HOUR}\n")
        
        while True:
            try:
                # Сброс счетчика раз в час
                if datetime.now() - self.last_reset > timedelta(hours=1):
                    self.reply_count = 0
                    self.last_reset = datetime.now()
                    print(f"🔄 Reply counter reset at {datetime.now().strftime('%H:%M:%S')}")
                
                # Проверка новых комментариев
                for comment in self.subreddit.stream.comments(skip_existing=True):
                    if comment.id in self.processed_comments:
                        continue
                    
                    if self.reply_count >= MAX_REPLIES_PER_HOUR:
                        print(f"⏸ Reply limit reached ({MAX_REPLIES_PER_HOUR}/hour). Waiting...")
                        time.sleep(CHECK_INTERVAL)
                        continue
                    
                    self.process_comment(comment)
                    self.processed_comments.add(comment.id)
                    
                    # Ограничение памяти
                    if len(self.processed_comments) > 1000:
                        self.processed_comments = set(list(self.processed_comments)[-500:])
                
            except KeyboardInterrupt:
                print("\n👋 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)
    
    def process_comment(self, comment):
        """Обработка одного комментария"""
        text = comment.body.lower()
        
        # Проверка триггеров
        if not any(trigger in text for trigger in ['!analyze', '!check', '!signal']):
            return
        
        # Парсинг символа
        symbol_reddit = self.parse_symbol(text)
        
        if not symbol_reddit:
            print(f"⚠️ Invalid symbol in comment by u/{comment.author}")
            return
        
        print(f"\n📊 Processing request from u/{comment.author}: {symbol_reddit}")
        
        try:
            # Анализ символа
            response = self.analyze_symbol(symbol_reddit)
            
            # Отправка ответа
            comment.reply(response)
            self.reply_count += 1
            
            print(f"✅ Replied to u/{comment.author} [{self.reply_count}/{MAX_REPLIES_PER_HOUR}]")
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            error_msg = f"❌ Error analyzing {symbol_reddit}: {str(e)[:100]}"
            print(error_msg)
            
            try:
                comment.reply(f"Sorry, I encountered an error analyzing {symbol_reddit}. Please try again later.")
            except:
                pass
    
    def parse_symbol(self, text):
        """Извлечение символа из текста"""
        words = text.upper().replace(',', ' ').replace('.', ' ').split()
        
        for word in words:
            # Проверка в маппинге
            if word in SYMBOL_MAP:
                return word
            
            # Проверка паттерна (3-6 букв/цифр)
            if 3 <= len(word) <= 6 and word.replace('-', '').isalnum():
                # Проверка популярных тикеров
                if word in ['SPY', 'QQQ', 'AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL', 'AMZN']:
                    return word
        
        return None
    
    def analyze_symbol(self, symbol_reddit):
        """Полный анализ символа"""
        # Маппинг символа
        symbol_yf = SYMBOL_MAP.get(symbol_reddit, symbol_reddit)
        
        # Определение типа актива
        asset_type = 'Gold'  # default
        for key, val in ASSET_TYPES.items():
            if key in symbol_reddit:
                asset_type = val
                break
        
        # Инициализация стратегии
        strategy = MultiAssetStrategy(symbol_yf, asset_type)
        
        # Получение данных
        if not strategy.fetch_data(period='3mo', interval='15m'):
            return f"❌ Unable to fetch data for **{symbol_reddit}**. Please check the symbol."
        
        # Бэктест
        backtest_results = strategy.backtest(lookback=100)
        
        # Текущий сигнал
        current_signal = strategy.get_current_signal()
        
        if not current_signal:
            return f"❌ No signal data available for **{symbol_reddit}**"
        
        # Генерация ответа через Claude
        analysis = self.generate_claude_analysis(
            symbol_reddit, 
            backtest_results, 
            current_signal
        )
        
        return analysis
    
    def generate_claude_analysis(self, symbol, backtest, signal):
        """Генерация анализа через Claude API"""
        
        # Определение уверенности
        winrate = backtest['winrate']
        confidence = "WAIT"
        
        if signal['type'] != 'WAIT':
            if winrate >= 70:
                confidence = "90%"
            elif winrate >= 60:
                confidence = "70%"
            elif winrate >= 50:
                confidence = "50%"
        
        signal_text = f"{signal['type']} {confidence}" if signal['type'] != 'WAIT' else "WAIT"
        
        # Промпт для Claude
        prompt = f"""Create a concise Reddit trading analysis for {symbol}:

**Performance (Last 100 trades):**
- Win Rate: {backtest['winrate']}%
- Total Trades: {backtest['total_trades']}
- Wins: {backtest['wins']} | Losses: {backtest['losses']}
- Profit Factor: {backtest.get('profit_factor', 0)}

**Current Signal:** {signal_text}
**Price:** {signal['price']}
**RSI:** {signal['rsi']} | **ADX:** {signal['adx']}
{f"**Entry:** {signal['price']}" if signal['type'] != 'WAIT' else ''}
{f"**Stop Loss:** {signal.get('stop_loss', 'N/A')}" if signal['type'] != 'WAIT' else ''}
{f"**Take Profit:** {signal.get('take_profit', 'N/A')}" if signal['type'] != 'WAIT' else ''}

Format as Reddit markdown. Requirements:
1. Start with ## 📊 {symbol} Analysis
2. Clear signal headline (BUY/SELL/WAIT with confidence)
3. Brief performance summary (1-2 sentences)
4. Current setup with SL/TP if applicable
5. 1-2 sentence market context
6. End with: "---\\n*Not financial advice | Multi-Asset Adaptive Strategy*"

Keep under 250 words. Professional but friendly tone.
"""
        
        try:
            message = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            # Fallback если Claude не работает
            print(f"⚠️ Claude API error: {e}")
            return self.generate_fallback_response(symbol, backtest, signal, confidence)
    
    def generate_fallback_response(self, symbol, backtest, signal, confidence):
        """Резервный ответ без Claude"""
        
        signal_emoji = "🟢" if signal['type'] == 'LONG' else "🔴" if signal['type'] == 'SHORT' else "⚪"
        
        response = f"""## 📊 {symbol} Analysis

{signal_emoji} **Current Signal:** {signal['type']} {confidence}

**Strategy Performance:**
- Win Rate: **{backtest['winrate']}%**
- Total Trades: {backtest['total_trades']} ({backtest['wins']}W / {backtest['losses']}L)
- Profit Factor: {backtest.get('profit_factor', 'N/A')}

**Market Context:**
- Price: ${signal['price']}
- RSI: {signal['rsi']} | ADX: {signal['adx']}
"""
        
        if signal['type'] != 'WAIT':
            response += f"""
**Trade Setup:**
- Entry: ${signal['price']}
- Stop Loss: ${signal.get('stop_loss', 'N/A')}
- Take Profit: ${signal.get('take_profit', 'N/A')}
- Risk/Reward: 1:1.5
"""
        else:
            response += "\n**Action:** No clear edge. Wait for better setup.\n"
        
        response += "\n---\n*Not financial advice | Multi-Asset Adaptive Strategy*"
        
        return response

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MULTI-ASSET TRADING BOT FOR REDDIT")
    print("=" * 60)
    print()
    
    # Проверка конфигурации
    if 'YOUR_' in REDDIT_CONFIG['client_id']:
        print("❌ ERROR: Please configure your Reddit API credentials in .env file")
        print("   Visit https://www.reddit.com/prefs/apps to create an app")
        exit(1)
    
    if 'YOUR_' in CLAUDE_API_KEY:
        print("❌ ERROR: Please configure your Anthropic API key in .env file")
        print("   Visit https://console.anthropic.com/ to get your key")
        exit(1)
    
    # Запуск бота
    bot = TradingRedditBot()
    bot.run()