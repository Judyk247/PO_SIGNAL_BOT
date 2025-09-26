import json
import logging
from utils.logger import setup_logger

logger = setup_logger('data_processor')

class DataProcessor:
    def __init__(self):
        self.message_buffer = []
        
    def process_message(self, message):
        """
        Process raw WebSocket messages for PocketOption
        Returns: Processed data or None if not relevant
        """
        try:
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            
            # Log the message for debugging
            logger.debug(f"Processing message: {message[:100]}...")
            
            # Handle different message types based on PocketOption protocol
            if message.startswith('42['):
                # This is a data message
                try:
                    json_data = json.loads(message[2:])
                    if isinstance(json_data, list) and len(json_data) > 0:
                        message_type = json_data[0]
                        
                        if message_type == "tick":
                            tick_data = json_data[1] if len(json_data) > 1 else {}
                            return self._process_tick_data(tick_data)
                            
                        elif message_type == "candles":
                            candles_data = json_data[1] if len(json_data) > 1 else {}
                            return self._process_candles_data(candles_data)
                            
                        elif message_type == "assets":
                            assets_data = json_data[1] if len(json_data) > 1 else {}
                            return self._process_assets_data(assets_data)
                            
                        elif message_type == "balance":
                            balance_data = json_data[1] if len(json_data) > 1 else {}
                            return self._process_balance_data(balance_data)
                            
                        elif message_type == "auth/success":
                            return {'type': 'auth_success', 'raw_data': json_data}
                            
                        elif message_type == "counters/all/success":
                            counters_data = json_data[1] if len(json_data) > 1 else {}
                            return self._process_counters_data(counters_data)
                
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON message: {message}")
                    return None
            
            # Handle ping messages
            elif message == '2':  # Ping from server
                return {'type': 'ping', 'action': 'respond'}
                
            elif message == '42["ping-server"]':  # PocketOption specific ping
                return {'type': 'ping_server', 'action': 'respond'}
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    def _process_tick_data(self, tick_data):
        """Process tick data messages for PocketOption"""
        if isinstance(tick_data, dict) and 'asset' in tick_data:
            return {
                'type': 'tick',
                'asset': tick_data['asset'],
                'price': tick_data.get('price'),
                'timestamp': tick_data.get('ts'),  # PocketOption uses 'ts' for timestamp
                'bid': tick_data.get('bid'),
                'ask': tick_data.get('ask'),
                'spread': tick_data.get('spread'),
                'raw_data': tick_data
            }
        return None
    
    def _process_candles_data(self, candles_data):
        """Process candles data for PocketOption"""
        if isinstance(candles_data, dict) and 'asset' in candles_data:
            return {
                'type': 'candles',
                'asset': candles_data['asset'],
                'timeframe': candles_data.get('period'),
                'candles': candles_data.get('candles', []),
                'from': candles_data.get('from'),
                'to': candles_data.get('to'),
                'raw_data': candles_data
            }
        return None
    
    def _process_assets_data(self, assets_data):
        """Process available assets list from PocketOption"""
        if isinstance(assets_data, list):
            return {
                'type': 'assets_list',
                'assets': assets_data,
                'count': len(assets_data),
                'raw_data': assets_data
            }
        elif isinstance(assets_data, dict) and 'instruments' in assets_data:
            return {
                'type': 'assets_list',
                'assets': assets_data.get('instruments', []),
                'count': len(assets_data.get('instruments', [])),
                'raw_data': assets_data
            }
        return None
    
    def _process_balance_data(self, balance_data):
        """Simple balance verification for NGN account"""
        if isinstance(balance_data, dict):
            currency = balance_data.get('currency', 'NGN')
            balance = balance_data.get('balance', 0)
            
            if currency == 'NGN':
                logger.info(f"✅ Connected to NGN Live Account | Balance: {balance:,.2f} NGN")
            else:
                logger.warning(f"⚠️  Unexpected currency: {currency} | Expected: NGN")
            
            return {'type': 'balance', 'currency': currency, 'balance': balance}
        return None
    
    def _process_counters_data(self, counters_data):
        """Process counters data (notifications, etc.)"""
        if isinstance(counters_data, dict):
            return {
                'type': 'counters',
                'pending_withdrawal': counters_data.get('pending-withdrawal', 0),
                'achievements': counters_data.get('achievements', 0),
                'support_tickets': counters_data.get('support', 0),
                'raw_data': counters_data
            }
        return None
    
    def get_trading_decision(self, processed_data):
        """
        Generate trading decisions based on processed data
        This will be expanded with your trading strategies
        """
        if processed_data and processed_data['type'] == 'tick':
            # Add your trading logic here
            asset = processed_data['asset']
            price = processed_data['price']
            
            # Example simple logic - replace with your strategies
            logger.debug(f"Tick received for {asset}: {price}")
            
        return None
