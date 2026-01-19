import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class MultiAssetStrategy:
    """
    Multi-Asset Adaptive Strategy
    Портировано из Pine Script
    """
    
    def __init__(self, symbol, asset_type='Gold'):
        self.symbol = symbol
        self.asset_type = asset_type
        self.volatility_adj = self._get_volatility_adj()
        self.data = None
        
    def _get_volatility_adj(self):
        """Адаптивная волатильность по типу актива"""
        vol_map = {
            'Gold': 1.0,
            'Silver': 1.2,
            'Palladium': 1.5,
            'Platinum': 1.3,
            'Bitcoin': 2.0,
            'Ethereum': 1.8
        }
        return vol_map.get(self.asset_type, 1.0)
    
    def fetch_data(self, period='3mo', interval='15m'):
        """Получение данных с Yahoo Finance"""
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                print(f"⚠️ No data for {self.symbol}")
                return False
            
            self.data = data
            return True
            
        except Exception as e:
            print(f"❌ Error fetching {self.symbol}: {e}")
            return False
    
    def calculate_atr(self, period=14):
        """Average True Range"""
        high = self.data['High']
        low = self.data['Low']
        close = self.data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean() * self.volatility_adj
        
        return atr
    
    def calculate_adx(self, period=14):
        """ADX (Average Directional Index)"""
        high = self.data['High']
        low = self.data['Low']
        close = self.data['Close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
    
    def calculate_rsi(self, period=14):
        """RSI (Relative Strength Index)"""
        delta = self.data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_indicators(self):
        df = self.data.copy()
        
        # ATR
        df['ATR'] = self.calculate_atr(14)
        
        # EMAs
        df['EMA_Fast'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=50, adjust=False).mean()
        df['EMA_Filter'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # ADX
        df['ADX'] = self.calculate_adx(14)
        
        # RSI
        df['RSI'] = self.calculate_rsi(14)
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2.0
        df['BB_Middle'] = df['Close'].rolling(bb_period).mean()
        df['BB_Std'] = df['Close'].rolling(bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * df['BB_Std'])
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * df['BB_Std'])
        
        # Volume
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['Volume_Spike'] = df['Volume'] > (df['Volume_SMA'] * 1.2)
        
        # Breakout levels
        df['Highest_High'] = df['High'].rolling(20).max()
        df['Lowest_Low'] = df['Low'].rolling(20).min()
        
        self.data = df
        return df
    
    def generate_signals(self):
        df = self.calculate_indicators()
        
        # Market Regime
        df['Is_Trending'] = df['ADX'] > 20
        df['Is_Ranging'] = df['ADX'] <= 20
        
        # Trend Direction
        df['Bullish_Trend'] = (df['EMA_Fast'] > df['EMA_Slow']) & (df['Close'] > df['EMA_Filter'])
        df['Bearish_Trend'] = (df['EMA_Fast'] < df['EMA_Slow']) & (df['Close'] < df['EMA_Filter'])
        
        # EMA Crossovers
        df['EMA_Cross_Up'] = (df['EMA_Fast'] > df['EMA_Slow']) & (df['EMA_Fast'].shift(1) <= df['EMA_Slow'].shift(1))
        df['EMA_Cross_Down'] = (df['EMA_Fast'] < df['EMA_Slow']) & (df['EMA_Fast'].shift(1) >= df['EMA_Slow'].shift(1))
        
        # === STRATEGY SIGNALS ===
        
        # 1. Trend Following
        df['Trend_Long'] = (
            df['Is_Trending'] & 
            df['Bullish_Trend'] & 
            df['EMA_Cross_Up'] & 
            df['Volume_Spike']
        )
        
        df['Trend_Short'] = (
            df['Is_Trending'] & 
            df['Bearish_Trend'] & 
            df['EMA_Cross_Down'] & 
            df['Volume_Spike']
        )
        
        # 2. Breakout
        df['Breakout_Long'] = (
            (df['Close'] > df['Highest_High'].shift(1)) & 
            df['Volume_Spike'] & 
            (df['Close'] > df['EMA_Filter'])
        )
        
        df['Breakout_Short'] = (
            (df['Close'] < df['Lowest_Low'].shift(1)) & 
            df['Volume_Spike'] & 
            (df['Close'] < df['EMA_Filter'])
        )
        
        # 3. Mean Reversion
        df['Mean_Rev_Long'] = (
            df['Is_Ranging'] & 
            (df['Close'] < df['BB_Lower']) & 
            (df['RSI'] < 30)
        )
        
        df['Mean_Rev_Short'] = (
            df['Is_Ranging'] & 
            (df['Close'] > df['BB_Upper']) & 
            (df['RSI'] > 70)
        )
        
        # Combined Signals
        df['Long_Signal'] = df['Trend_Long'] | df['Breakout_Long'] | df['Mean_Rev_Long']
        df['Short_Signal'] = df['Trend_Short'] | df['Breakout_Short'] | df['Mean_Rev_Short']
        
        self.data = df
        return df
    
    def backtest(self, lookback=100):
        """Бэктест стратегии (последние N сделок)"""
        df = self.generate_signals()
        
        trades = []
        i = len(df) - lookback
        
        while i < len(df) - 1:
            if df['Long_Signal'].iloc[i]:
                trade = self._execute_trade(df, i, 'LONG')
                if trade:
                    trades.append(trade)
                    i = trade['exit_idx'] + 1  
                else:
                    i += 1
                    
            elif df['Short_Signal'].iloc[i]:
                trade = self._execute_trade(df, i, 'SHORT')
                if trade:
                    trades.append(trade)
                    i = trade['exit_idx'] + 1
                else:
                    i += 1
            else:
                i += 1
        
        # Статистика
        wins = sum(1 for t in trades if t['profit'] > 0)
        losses = sum(1 for t in trades if t['profit'] <= 0)
        total = len(trades)
        
        winrate = (wins / total * 100) if total > 0 else 0
        
        avg_win = np.mean([t['profit'] for t in trades if t['profit'] > 0]) if wins > 0 else 0
        avg_loss = np.mean([abs(t['profit']) for t in trades if t['profit'] < 0]) if losses > 0 else 0
        
        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'winrate': round(winrate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
            'trades': trades
        }
    
    def _execute_trade(self, df, entry_idx, direction):
        """Симуляция сделки с SL/TP"""
        entry_price = df['Close'].iloc[entry_idx]
        atr = df['ATR'].iloc[entry_idx]
        
        if pd.isna(atr) or atr == 0:
            return None
        
        # Stop Loss & Take Profit 
        stop_atr_mult = 2.0
        tp_atr_mult = 2.0
        
        if direction == 'LONG':
            sl = entry_price - (atr * stop_atr_mult)
            tp = entry_price + (atr * tp_atr_mult)
        else:
            sl = entry_price + (atr * stop_atr_mult)
            tp = entry_price - (atr * tp_atr_mult)
        
        max_bars = min(entry_idx + 100, len(df))
        
        for i in range(entry_idx + 1, max_bars):
            if direction == 'LONG':
                if df['Low'].iloc[i] <= sl:
                    return {
                        'entry': entry_price,
                        'exit': sl,
                        'profit': ((sl - entry_price) / entry_price) * 100,
                        'exit_type': 'SL',
                        'exit_idx': i,
                        'direction': direction
                    }
                elif df['High'].iloc[i] >= tp:
                    return {
                        'entry': entry_price,
                        'exit': tp,
                        'profit': ((tp - entry_price) / entry_price) * 100,
                        'exit_type': 'TP',
                        'exit_idx': i,
                        'direction': direction
                    }
            else:  # SHORT
                if df['High'].iloc[i] >= sl:
                    return {
                        'entry': entry_price,
                        'exit': sl,
                        'profit': ((entry_price - sl) / entry_price) * 100,
                        'exit_type': 'SL',
                        'exit_idx': i,
                        'direction': direction
                    }
                elif df['Low'].iloc[i] <= tp:
                    return {
                        'entry': entry_price,
                        'exit': tp,
                        'profit': ((entry_price - tp) / entry_price) * 100,
                        'exit_type': 'TP',
                        'exit_idx': i,
                        'direction': direction
                    }
        
        # Timeout
        return {
            'entry': entry_price,
            'exit': df['Close'].iloc[max_bars - 1],
            'profit': 0,
            'exit_type': 'TIMEOUT',
            'exit_idx': max_bars - 1,
            'direction': direction
        }
    
    def get_current_signal(self):
        """Получить текущий сигнал"""
        if self.data is None or self.data.empty:
            return None
        
        last = self.data.iloc[-1]
        
        signal = {
            'timestamp': last.name,
            'price': round(last['Close'], 2),
            'atr': round(last['ATR'], 2) if not pd.isna(last['ATR']) else 0,
            'rsi': round(last['RSI'], 1) if not pd.isna(last['RSI']) else 50,
            'adx': round(last['ADX'], 1) if not pd.isna(last['ADX']) else 0,
            'type': 'WAIT'
        }
        
        if last['Long_Signal']:
            signal['type'] = 'LONG'
            signal['stop_loss'] = round(signal['price'] - (signal['atr'] * 2.0), 2)
            signal['take_profit'] = round(signal['price'] + (signal['atr'] * 3.0), 2)
        elif last['Short_Signal']:
            signal['type'] = 'SHORT'
            signal['stop_loss'] = round(signal['price'] + (signal['atr'] * 2.0), 2)
            signal['take_profit'] = round(signal['price'] - (signal['atr'] * 3.0), 2)
        
        return signal