import pandas as pd
from strategies.trend_reversal import TrendReversalStrategy
from strategies.trend_following import TrendFollowingStrategy
from utils.logger import setup_logger

logger = setup_logger('strategy_engine')

class StrategyEngine:
    def __init__(self, data_processor):
        self.data_processor = data_processor
        self.strategies = {}
        self.signals = []
        self.max_signals_history = 100
        
        # Initialize ALL strategies
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        # Trend Reversal Strategy for 5m timeframe
        self.strategies['trend_reversal_5m'] = TrendReversalStrategy(timeframe='5m')
        
        # Trend Following Strategies for shorter timeframes
        self.strategies['trend_following_1m'] = TrendFollowingStrategy(timeframe='1m')
        self.strategies['trend_following_2m'] = TrendFollowingStrategy(timeframe='2m')
        self.strategies['trend_following_3m'] = TrendFollowingStrategy(timeframe='3m')
    
    def process_data(self, processed_data):
        """
        Process data and generate trading signals for PocketOption
        Returns: Signal dict or None
        """
        try:
            if not processed_data:
                return None
                
            data_type = processed_data.get('type')
            
            if data_type == 'tick':
                return self._process_tick_signal(processed_data)
                
            elif data_type == 'candles':  # Changed from 'instrument_update' to 'candles'
                return self._process_candles_signal(processed_data)  # Renamed method
                
            return None
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return None
    
    def _process_tick_signal(self, tick_data):
        """Process tick data for signals - more useful for PocketOption"""
        asset = tick_data.get('asset', '')
        price = tick_data.get('price', 0)
        bid = tick_data.get('bid', 0)
        ask = tick_data.get('ask', 0)
        
        logger.debug(f"Processing tick: {asset} | Price: {price} | Bid/Ask: {bid}/{ask}")
        
        # For PocketOption, tick data can be more relevant for certain strategies
        # You might want to implement tick-based strategies here
        # For now, return None as we focus on candle-based strategies
        return None
    
    def _process_candles_signal(self, candles_data):  # Renamed from _process_ohlc_signal
        """Process candles data for signals using our strategies"""
        asset = candles_data.get('asset', '')
        candles = candles_data.get('candles', [])
        timeframe = candles_data.get('timeframe', '5m')  # Changed from 'period' to 'timeframe'
        
        logger.debug(f"Processing candles: {asset} with {len(candles)} candles (TF: {timeframe})")
        
        # Convert candles to DataFrame for our strategies
        if candles and len(candles) > 0:
            df = self._candles_to_dataframe(candles)
            
            if df.empty:
                return None
            
            # Run appropriate strategy based on timeframe
            signal = self._run_strategy_for_timeframe(df, timeframe)
            
            # Add asset and timeframe to signal
            if signal and signal.get('signal') != 'hold':
                signal['asset'] = asset
                signal['timeframe'] = timeframe
                signal['timestamp'] = pd.Timestamp.now()  # Add current timestamp
                self._store_signal(signal)
                
                logger.info(f"📈 Signal generated: {signal['signal'].upper()} for {asset} ({timeframe}) "
                           f"| Confidence: {signal.get('confidence', 0)}%")
                return signal
        
        return None
    
    def _run_strategy_for_timeframe(self, df, timeframe):
        """Run the appropriate strategy based on timeframe"""
        strategy_key = None
        
        if timeframe == '5m':
            strategy_key = 'trend_reversal_5m'
        elif timeframe == '1m':
            strategy_key = 'trend_following_1m'
        elif timeframe == '2m':
            strategy_key = 'trend_following_2m'
        elif timeframe == '3m':
            strategy_key = 'trend_following_3m'
        
        if strategy_key and strategy_key in self.strategies:
            try:
                return self.strategies[strategy_key].analyze(df)
            except Exception as e:
                logger.error(f"Error running strategy {strategy_key}: {e}")
        
        return {'signal': 'hold', 'confidence': 0}
    
    def _candles_to_dataframe(self, candles):
        """Convert PocketOption candles list to pandas DataFrame"""
        if not candles:
            return pd.DataFrame()
            
        try:
            # PocketOption candle format might be: [timestamp, open, high, low, close, volume]
            # OR could be objects with keys - we need to handle both
            if isinstance(candles[0], (list, tuple)):
                # List format: [timestamp, open, high, low, close, volume]
                df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')  # Assuming Unix timestamp
                
            elif isinstance(candles[0], dict):
                # Dictionary format: {ts, open, high, low, close, volume}
                df = pd.DataFrame(candles)
                if 'ts' in df.columns:  # PocketOption uses 'ts' for timestamp
                    df['timestamp'] = pd.to_datetime(df['ts'], unit='s')
                elif 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                else:
                    # Create a timestamp index if no timestamp provided
                    df['timestamp'] = pd.date_range(start=pd.Timestamp.now() - pd.Timedelta(minutes=len(df)), 
                                                   periods=len(df), freq='T')
            
            else:
                logger.warning(f"Unknown candle format: {type(candles[0])}")
                return pd.DataFrame()
            
            df.set_index('timestamp', inplace=True)
            
            # Ensure numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting candles to DataFrame: {e}")
            return pd.DataFrame()
    
    def _store_signal(self, signal):
        """Store signal in history"""
        self.signals.append(signal)
        if len(self.signals) > self.max_signals_history:
            self.signals = self.signals[-self.max_signals_history:]
    
    def get_recent_signals(self, count=10):
        """Get recent signals"""
        return self.signals[-count:] if self.signals else []
    
    def get_signals_by_asset(self, asset):
        """Get signals for a specific asset"""
        return [s for s in self.signals if s.get('asset') == asset]
    
    def clear_signals(self):
        """Clear all signals history"""
        self.signals = []
