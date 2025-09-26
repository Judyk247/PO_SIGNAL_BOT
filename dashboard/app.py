import os
from flask import Flask, jsonify, request, send_file
from flask_socketio import SocketIO
import json

# Get absolute path to templates
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
INDEX_PATH = os.path.join(TEMPLATE_DIR, 'index.html')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

class Dashboard:
    def __init__(self):
        self.signals = []
        self.performance = {
            'total_signals': 0,
            'winning_signals': 0,
            'losing_signals': 0,
            'total_profit': 0,
            'active_assets': set(),
            'connection_status': 'disconnected'
        }
        self.connection_stats = {
            'websocket_connected': False,
            'authenticated': False,
            'last_message': None,
            'message_count': 0
        }
    
    def add_signal(self, signal):
        formatted_signal = {
            'id': len(self.signals) + 1,
            'asset': signal.get('asset', 'Unknown'),
            'direction': signal.get('signal', 'hold').upper(),
            'confidence': signal.get('confidence', 0),
            'timestamp': signal.get('timestamp', ''),
            'timeframe': signal.get('timeframe', ''),
            'type': signal.get('type', 'unknown')
        }
        
        self.signals.insert(0, formatted_signal)
        self.signals = self.signals[:20]  # Keep only recent 20 signals
        
        # Track active assets
        if formatted_signal['asset'] != 'Unknown':
            self.performance['active_assets'].add(formatted_signal['asset'])
        
        self.performance['total_signals'] += 1
        
        socketio.emit('new_signal', formatted_signal)
        socketio.emit('performance_update', self.performance)
    
    def update_connection_status(self, status_data):
        """Update WebSocket connection status"""
        self.connection_stats.update(status_data)
        self.performance['connection_status'] = 'connected' if status_data.get('websocket_connected') else 'disconnected'
        
        socketio.emit('connection_update', self.connection_stats)
        socketio.emit('performance_update', self.performance)

# Global dashboard instance
dashboard = Dashboard()

@app.route('/')
def index():
    """Serve dashboard HTML - guaranteed to work"""
    try:
        # Try to find the template file
        possible_paths = [
            '/opt/render/project/src/templates/index.html',  # Render path
            os.path.join(os.path.dirname(__file__), 'templates', 'index.html'),  # Relative path
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'index.html'),  # Main directory
            'templates/index.html'  # Current directory
        ]
        
        for template_path in possible_paths:
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read(), 200, {'Content-Type': 'text/html'}
        
        # If no template found, CREATE IT PROGRAMMATICALLY
        return create_fallback_dashboard()
        
    except Exception as e:
        return create_fallback_dashboard()

def create_fallback_dashboard():
    """Create dashboard HTML programmatically as fallback"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PocketOption Trading Bot Dashboard</title>
        <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f4f4f4; }
            .header { background: #4a6baf; color: white; padding: 20px; border-radius: 5px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: white; padding: 20px; border-radius: 5px; text-align: center; }
            .connection-status { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
            .signal { padding: 10px; border-bottom: 1px solid #eee; display: grid; grid-template-columns: 1fr 1fr 1fr 1fr 1fr; }
            .profit { color: green; font-weight: bold; }
            .loss { color: red; font-weight: bold; }
            .connected { color: green; }
            .disconnected { color: red; }
            .call { background-color: #d4edda; }
            .put { background-color: #f8d7da; }
            .hold { background-color: #fff3cd; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 PocketOption Trading Bot Dashboard</h1>
            <p>Real-time trading signals and connection monitoring</p>
        </div>
        
        <div class="connection-status">
            <div class="stat-card">
                <h3>🔌 Connection Status</h3>
                <div id="connection-status" class="disconnected">Disconnected</div>
                <div id="authentication-status">Not Authenticated</div>
            </div>
            <div class="stat-card">
                <h3>📨 Message Count</h3>
                <div id="message-count">0</div>
                <small>WebSocket messages received</small>
            </div>
            <div class="stat-card">
                <h3>⚡ Last Activity</h3>
                <div id="last-activity">Never</div>
                <small>Last message timestamp</small>
            </div>
            <div class="stat-card">
                <h3>🎯 Active Assets</h3>
                <div id="active-assets">0</div>
                <small>Assets with signals</small>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card"><h3>Total Signals</h3><div id="total-signals">0</div></div>
            <div class="stat-card"><h3>Winning Signals</h3><div id="winning-signals" class="profit">0</div></div>
            <div class="stat-card"><h3>Losing Signals</h3><div id="losing-signals" class="loss">0</div></div>
            <div class="stat-card"><h3>Total Profit</h3><div id="total-profit" class="profit">$0.00</div></div>
            <div class="stat-card"><h3>Win Rate</h3><div id="win-rate">0%</div></div>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 5px;">
            <h2>📈 Recent Trading Signals</h2>
            <div class="signal" style="font-weight: bold; background: #f8f9fa;">
                <div>Time</div><div>Asset</div><div>Signal</div><div>Timeframe</div><div>Confidence</div>
            </div>
            <div id="signals-container"></div>
        </div>
        
        <script>
            const socket = io();
            
            // Handle connection status updates
            socket.on('connection_update', function(stats) {
                document.getElementById('connection-status').textContent = 
                    stats.websocket_connected ? '✅ Connected' : '❌ Disconnected';
                document.getElementById('connection-status').className = 
                    stats.websocket_connected ? 'connected' : 'disconnected';
                
                document.getElementById('authentication-status').textContent = 
                    stats.authenticated ? '✅ Authenticated' : '❌ Not Authenticated';
                document.getElementById('message-count').textContent = stats.message_count;
                document.getElementById('last-activity').textContent = 
                    stats.last_message || 'Never';
            });
            
            // Handle new trading signals
            socket.on('new_signal', function(signal) {
                const container = document.getElementById('signals-container');
                const signalElement = document.createElement('div');
                signalElement.className = 'signal ' + signal.direction.toLowerCase();
                signalElement.innerHTML = `
                    <div>${new Date(signal.timestamp).toLocaleTimeString()}</div>
                    <div>${signal.asset}</div>
                    <div class="${signal.direction.toLowerCase()}">${signal.direction}</div>
                    <div>${signal.timeframe}</div>
                    <div>${signal.confidence}%</div>
                `;
                container.insertBefore(signalElement, container.firstChild);
                
                // Limit to 20 signals
                if (container.children.length > 20) {
                    container.removeChild(container.lastChild);
                }
            });
            
            // Handle performance updates
            socket.on('performance_update', function(data) {
                document.getElementById('total-signals').textContent = data.total_signals;
                document.getElementById('winning-signals').textContent = data.winning_signals;
                document.getElementById('losing-signals').textContent = data.losing_signals;
                document.getElementById('total-profit').textContent = '$' + data.total_profit.toFixed(2);
                document.getElementById('active-assets').textContent = data.active_assets ? data.active_assets.size : 0;
                
                const winRate = data.total_signals > 0 ? 
                    ((data.winning_signals / data.total_signals) * 100).toFixed(1) : 0;
                document.getElementById('win-rate').textContent = winRate + '%';
            });
            
            // Request initial data
            socket.emit('get_initial_data');
        </script>
    </body>
    </html>
    """
    return html_content, 200, {'Content-Type': 'text/html'}

@app.route('/debug/filesystem')
def debug_filesystem():
    """Debug the entire filesystem structure"""
    import os
    base_dir = os.path.dirname(os.path.dirname(__file__))
    
    def list_files(startpath):
        file_tree = {}
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 2 * level
            file_tree[os.path.basename(root)] = {
                'files': files,
                'path': root
            }
        return file_tree
    
    return jsonify({
        'current_working_dir': os.getcwd(),
        'base_dir': base_dir,
        'filesystem': list_files('/opt/render/project/src'),
        'templates_exists': os.path.exists('/opt/render/project/src/templates'),
        'dashboard_files': os.listdir(os.path.dirname(__file__)) if os.path.exists(os.path.dirname(__file__)) else 'NOT_FOUND'
    })

# Debug endpoint to check file existence
@app.route('/debug/files')
def debug_files():
    files = {
        'base_dir': BASE_DIR,
        'template_dir': TEMPLATE_DIR,
        'index_path': INDEX_PATH,
        'index_exists': os.path.exists(INDEX_PATH),
        'current_dir_files': os.listdir('.'),
        'template_dir_files': os.listdir(TEMPLATE_DIR) if os.path.exists(TEMPLATE_DIR) else 'NOT FOUND'
    }
    return jsonify(files)

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'PocketOption Trading Bot',
        'signals_count': len(dashboard.signals)
    })

@app.route('/api/signals')
def get_signals():
    return jsonify(dashboard.signals)

@app.route('/api/performance')
def get_performance():
    return jsonify(dashboard.performance)

@app.route('/api/connection')
def get_connection_status():
    return jsonify(dashboard.connection_stats)

@socketio.on('connect')
def handle_connect():
    socketio.emit('clients_update', len(socketio.server.manager.rooms))
    # Send current connection status to newly connected client
    socketio.emit('connection_update', dashboard.connection_stats)

@socketio.on('disconnect')
def handle_disconnect():
    socketio.emit('clients_update', len(socketio.server.manager.rooms))

@socketio.on('get_initial_data')
def handle_initial_data():
    """Send all current data to newly connected client"""
    socketio.emit('connection_update', dashboard.connection_stats)
    socketio.emit('performance_update', dashboard.performance)
    # Send recent signals
    for signal in dashboard.signals[:10]:
        socketio.emit('new_signal', signal)
