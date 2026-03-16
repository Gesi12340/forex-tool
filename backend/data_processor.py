import pandas as pd
import numpy as np

class DataProcessor:
    """
    Processes real-time market data and calculates technical indicators.
    """
    def __init__(self):
        pass

    def prepare_dataframe(self, candles):
        """Converts raw candle list to Pandas DataFrame."""
        df = pd.DataFrame([{
            'time': c['time'],
            'open': float(c['mid']['o']),
            'high': float(c['mid']['h']),
            'low': float(c['mid']['l']),
            'close': float(c['mid']['c']),
            'volume': c['volume']
        } for c in candles])
        df['time'] = pd.to_datetime(df['time'])
        return df

    def add_indicators(self, df):
        """Calculates RSI, EMA, MACD, ADX, ATR, and ROC."""
        # Exponential Moving Averages
        df['ema_fast'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=26, adjust=False).mean()
        
        # MACD
        df['macd'] = df['ema_fast'] - df['ema_slow']
        df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR (Average True Range) for Volatility
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        # ADX (Average Directional Index) for Trend Strength
        df['up_move'] = df['high'] - df['high'].shift(1)
        df['down_move'] = df['low'].shift(1) - df['low']
        df['p_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
        df['m_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
        
        df['p_di'] = 100 * (df['p_dm'].ewm(alpha=1/14).mean() / df['tr'].ewm(alpha=1/14).mean())
        df['m_di'] = 100 * (df['m_dm'].ewm(alpha=1/14).mean() / df['tr'].ewm(alpha=1/14).mean())
        df['dx'] = 100 * abs(df['p_di'] - df['m_di']) / (df['p_di'] + df['m_di'])
        df['adx'] = df['dx'].ewm(alpha=1/14).mean()
        
        # ROC (Rate of Change) for Price Velocity
        df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        # Bollinger Bands
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['std_20'] = df['close'].rolling(window=20).std()
        df['upper_band'] = df['sma_20'] + (df['std_20'] * 2)
        df['lower_band'] = df['sma_20'] - (df['std_20'] * 2)
        
        # Cleanup temp columns
        df.drop(['h_l', 'h_pc', 'l_pc', 'tr', 'up_move', 'down_move', 'p_dm', 'm_dm', 'p_di', 'm_di', 'dx'], axis=1, inplace=True)
        
        return df.dropna()

    def get_latest_features(self, df):
        """Returns the most recent row as a feature dictionary."""
        return df.iloc[-1].to_dict()
