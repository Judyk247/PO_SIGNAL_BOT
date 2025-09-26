import websocket
import json
import threading
import time
import logging
import base64
import os
from config.credentials import Credentials
from utils.logger import setup_logger

logger = setup_logger('websocket_client')

class PocketOptionWebSocketClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.authenticated = False
        self.ping_interval = 25000
        self.ping_timeout = 20000
        self.sid = None
        self.message_count = 0
        self.on_message_callback = None
        self.available_assets = set()  # Dynamic asset tracking
        self.received_data_types = set()  # Track what data PocketOption sends
        
    def get_manual_session_token(self):
        """Get session token for PocketOption"""
        logger.info("🔐 Using manually provided SESSION_TOKEN from environment variables")
        return Credentials.SESSION_TOKEN

    def on_open(self, ws):
        logger.info("✅ WebSocket connected to PocketOption")
        self.connected = True

    def on_message(self, ws, message):
        try:
            self.message_count += 1
            
            if isinstance(message, bytes):
                message = message.decode('utf-8')

            logger.debug(f"Received #{self.message_count}: {message[:200]}...")

            # Handle different message types based on PocketOption protocol
            if message.startswith('0{'):
                conn_info = json.loads(message[1:])
                self.sid = conn_info.get('sid')
                self.ping_interval = conn_info.get('pingInterval', 25000)
                self.ping_timeout = conn_info.get('pingTimeout', 20000)
                logger.info(f"Connection established. SID: {self.sid}")

            elif message == '40':
                logger.info("Namespace connected, sending PocketOption authentication")
                auth_data = {
                    "sessionToken": Credentials.SESSION_TOKEN,
                    "uid": Credentials.USER_ID,
                    "lang": "en",
                    "currentUrl": "cabinet",
                    "isChart": 1
                }
                auth_msg = f'42["auth",{json.dumps(auth_data)}]'
                ws.send(auth_msg)
                logger.debug(f"Sent: {auth_msg}")

            elif message.startswith('42['):
                try:
                    json_data = json.loads(message[2:])
                    self.handle_data_message(json_data)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON: {message}")

            elif message == '2':
                ws.send('3')  # Pong response
                logger.debug("Sent pong response")

            elif message == '42["ping-server"]':
                ws.send('3')  # Pong response
                logger.debug("Responded to ping-server")

            else:
                logger.debug(f"Unhandled message: {message}")

            # Send raw message to callback for processing
            if self.on_message_callback:
                self.on_message_callback(message)

        except Exception as e:
            logger.error(f"Message processing error: {e}")

    def handle_data_message(self, data):
        """Handle all incoming data messages dynamically"""
        if not isinstance(data, list) or len(data) == 0:
            return

        message_type = data[0]
        message_data = data[1] if len(data) > 1 else {}

        # Track what types of data PocketOption sends us
        self.received_data_types.add(message_type)
        
        logger.info(f"📨 Received message type: {message_type}")

        if message_type == "auth/success":
            logger.info("✅ PocketOption authentication successful!")
            self.authenticated = True
            # Don't auto-subscribe - wait for PocketOption to push data
            logger.info("🔄 Waiting for PocketOption data streams...")
            self._log_data_patterns()

        elif message_type == "auth":
            logger.info(f"Auth response: {message_data}")

        elif message_type == "assets":
            self._handle_assets_message(message_data)

        elif message_type == "tick":
            self._handle_tick_message(message_data)

        elif message_type == "candles":
            self._handle_candles_message(message_data)

        elif message_type == "quotes":
            self._handle_quotes_message(message_data)

        elif message_type == "balance":
            self._handle_balance_message(message_data)

        elif message_type == "counters/all/success":
            logger.debug(f"Counters update: {message_data}")

        else:
            # Log unknown message types to understand PocketOption's API
            logger.info(f"🔍 Unknown message type: {message_type} - Data: {message_data}")

    def _handle_assets_message(self, assets_data):
        """Dynamically handle assets list if provided"""
        if isinstance(assets_data, list) and assets_data:
            logger.info(f"🎯 Received {len(assets_data)} assets")
            self.available_assets.update(assets_data)
            self._update_trading_settings()
        elif isinstance(assets_data, dict) and 'instruments' in assets_data:
            instruments = assets_data.get('instruments', [])
            logger.info(f"🎯 Received {len(instruments)} instruments")
            self.available_assets.update(instruments)
            self._update_trading_settings()

    def _handle_tick_message(self, tick_data):
        """Handle tick data dynamically"""
        if isinstance(tick_data, dict):
            asset = tick_data.get('asset', 'unknown')
            price = tick_data.get('price', 0)
            
            # Track asset from tick data
            if asset and asset != 'unknown':
                self.available_assets.add(asset)
                
            logger.debug(f"📈 Tick: {asset} = {price}")

    def _handle_candles_message(self, candles_data):
        """Handle candles data dynamically"""
        if isinstance(candles_data, dict):
            asset = candles_data.get('asset', 'unknown')
            candles = candles_data.get('candles', [])
            
            # Track asset from candles data
            if asset and asset != 'unknown':
                self.available_assets.add(asset)
                
            logger.debug(f"📊 Candles: {asset} - {len(candles)} candles")

    def _handle_quotes_message(self, quotes_data):
        """Handle quotes data if provided"""
        if isinstance(quotes_data, dict):
            asset = quotes_data.get('asset', 'unknown')
            # Track asset from quotes data
            if asset and asset != 'unknown':
                self.available_assets.add(asset)
            logger.debug(f"💹 Quotes: {quotes_data}")

    def _handle_balance_message(self, balance_data):
        """Handle balance updates"""
        if isinstance(balance_data, dict):
            currency = balance_data.get('currency', 'NGN')
            balance = balance_data.get('balance', 0)
            logger.info(f"💰 Balance update: {balance:,.2f} {currency}")

    def _update_trading_settings(self):
        """Dynamically update trading settings with discovered assets"""
        try:
            from config.settings import TRADING_SETTINGS
            
            if self.available_assets:
                # Convert set to list and take reasonable number of assets
                assets_list = list(self.available_assets)[:50]  # Limit to 50 assets
                TRADING_SETTINGS['assets'] = assets_list
                logger.info(f"🔄 Updated trading settings with {len(assets_list)} assets")
                
        except Exception as e:
            logger.error(f"Error updating trading settings: {e}")

    def _log_data_patterns(self):
        """Log what data patterns we're observing from PocketOption"""
        logger.info(f"📊 Observed data types: {list(self.received_data_types)}")
        logger.info(f"🎯 Discovered assets: {len(self.available_assets)}")
        
        if self.available_assets:
            sample_assets = list(self.available_assets)[:5]
            logger.info(f"🔍 Sample assets: {sample_assets}")

    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        self.connected = False
        self.authenticated = False

    def on_close(self, ws, close_status_code, close_msg):
        logger.info(f"WebSocket connection closed: {close_msg}")
        self.connected = False
        self.authenticated = False

    def connect(self):
        """Connect to PocketOption WebSocket"""
        try:
            Credentials.validate()
            logger.info("Credentials validated. Proceeding with connection...")

            key = base64.b64encode(os.urandom(16)).decode('utf-8')

            headers = [
                "Host: events-po.com",
                "Connection: Upgrade",
                "Pragma: no-cache",
                "Cache-Control: no-cache",
                "User-Agent: Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
                "Upgrade: websocket",
                "Origin: https://m.pocketoption.com",
                "Sec-WebSocket-Version: 13",
                "Accept-Encoding: gzip, deflate, br, zstd",
                "Accept-Language: en-US,en;q=0.9",
                f"Sec-WebSocket-Key: {key}",
                "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits"
            ]

            self.ws = websocket.WebSocketApp(
                Credentials.WS_URL,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                header=headers
            )

            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()

            for i in range(50):
                if self.connected:
                    return True
                time.sleep(0.1)

            logger.error("WebSocket connection timeout")
            return False

        except ValueError as e:
            logger.error(f"Credential validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def subscribe_to_assets(self):
        """REMOVED - PocketOption will push data automatically"""
        logger.info("🔄 Passive mode: Waiting for PocketOption to push data streams...")
        # No active subscriptions - let PocketOption control the data flow

    def keep_alive(self):
        """Keep WebSocket connection alive"""
        while self.connected:
            try:
                time.sleep(self.ping_interval / 1000)
            except Exception as e:
                logger.error(f"Keep alive error: {e}")
                time.sleep(5)

    def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws:
            self.ws.close()
            self.connected = False
            self.authenticated = False
            logger.info("Disconnected from PocketOption WebSocket")
