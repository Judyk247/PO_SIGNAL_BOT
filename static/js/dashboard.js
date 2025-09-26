// dashboard/static/js/dashboard.js
class PocketOptionDashboard {
    constructor() {
        this.socket = io();
        this.performanceChart = null;
        this.distributionChart = null;
        this.signals = [];
        this.connectionStats = {
            websocket_connected: false,
            authenticated: false,
            last_message: null,
            message_count: 0
        };
        this.performanceData = {
            total_signals: 0,
            winning_signals: 0,
            losing_signals: 0,
            total_profit: 0,
            active_assets: 0,
            connection_status: 'disconnected'
        };
        
        this.init();
    }

    init() {
        this.initializeCharts();
        this.setupSocketListeners();
        this.loadInitialData();
        this.setupEventListeners();
        
        // Update timestamp every minute
        setInterval(() => {
            this.updateLastUpdateTime();
        }, 60000);
    }

    initializeCharts() {
        // Performance Chart
        const performanceCtx = document.getElementById('performance-chart');
        if (performanceCtx) {
            this.performanceChart = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Account Balance',
                        data: [],
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#27ae60',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Performance Trend',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }

        // Distribution Chart
        const distributionCtx = document.getElementById('distribution-chart');
        if (distributionCtx) {
            this.distributionChart = new Chart(distributionCtx, {
                type: 'doughnut',
                data: {
                    labels: ['CALL Signals', 'PUT Signals', 'HOLD Signals'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#27ae60', '#e74c3c', '#f39c12'],
                        borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                        borderWidth: 2,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'Signal Distribution',
                            font: {
                                size: 16,
                                weight: 'bold'
                            }
                        }
                    }
                }
            });
        }
    }

    setupSocketListeners() {
        // Connection status updates
        this.socket.on('connection_update', (stats) => {
            this.connectionStats = stats;
            this.updateConnectionStatus();
        });

        // Performance updates
        this.socket.on('performance_update', (data) => {
            this.performanceData = data;
            this.updatePerformanceStats();
            this.updateCharts();
        });

        // New signals
        this.socket.on('new_signal', (signal) => {
            this.addSignalToUI(signal);
            this.showNotification(`New ${signal.direction} signal for ${signal.asset}`);
        });

        // Socket connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.socket.emit('get_initial_data');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus();
        });
    }

    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadInitialData();
            });
        }

        // Filter signals
        const filterAsset = document.getElementById('filter-asset');
        if (filterAsset) {
            filterAsset.addEventListener('change', (e) => {
                this.filterSignals(e.target.value);
            });
        }

        // Search functionality
        const searchSignals = document.getElementById('search-signals');
        if (searchSignals) {
            searchSignals.addEventListener('input', (e) => {
                this.searchSignals(e.target.value);
            });
        }
    }

    async loadInitialData() {
        try {
            // Load signals
            const signalsResponse = await fetch('/api/signals');
            this.signals = await signalsResponse.json();
            this.displaySignals(this.signals);

            // Load performance data
            const performanceResponse = await fetch('/api/performance');
            this.performanceData = await performanceResponse.json();
            this.updatePerformanceStats();

            // Load connection status
            const connectionResponse = await fetch('/api/connection');
            this.connectionStats = await connectionResponse.json();
            this.updateConnectionStatus();

            this.updateCharts();

        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data', 'error');
        }
    }

    updateConnectionStatus() {
        const connectionStatus = document.getElementById('connection-status');
        const authStatus = document.getElementById('authentication-status');
        const messageCount = document.getElementById('message-count');
        const lastActivity = document.getElementById('last-activity');

        if (connectionStatus) {
            connectionStatus.textContent = this.connectionStats.websocket_connected ? 
                '✅ Connected' : '❌ Disconnected';
            connectionStatus.className = this.connectionStats.websocket_connected ? 
                'connected' : 'disconnected';
        }

        if (authStatus) {
            authStatus.textContent = this.connectionStats.authenticated ? 
                '✅ Authenticated' : '❌ Not Authenticated';
            authStatus.className = this.connectionStats.authenticated ? 
                'authenticated' : 'not-authenticated';
        }

        if (messageCount) {
            messageCount.textContent = this.connectionStats.message_count || 0;
        }

        if (lastActivity) {
            lastActivity.textContent = this.connectionStats.last_message || 'Never';
        }
    }

    updatePerformanceStats() {
        const { total_signals, winning_signals, losing_signals, total_profit, active_assets } = this.performanceData;
        
        const totalSignalsEl = document.getElementById('total-signals');
        const winningSignalsEl = document.getElementById('winning-signals');
        const losingSignalsEl = document.getElementById('losing-signals');
        const totalProfitEl = document.getElementById('total-profit');
        const winRateEl = document.getElementById('win-rate');
        const activeAssetsEl = document.getElementById('active-assets');

        if (totalSignalsEl) totalSignalsEl.textContent = total_signals;
        if (winningSignalsEl) winningSignalsEl.textContent = winning_signals;
        if (losingSignalsEl) losingSignalsEl.textContent = losing_signals;
        if (totalProfitEl) totalProfitEl.textContent = `$${total_profit.toFixed(2)}`;
        if (activeAssetsEl) activeAssetsEl.textContent = active_assets || 0;
        
        if (winRateEl) {
            const winRate = total_signals > 0 ? 
                ((winning_signals / total_signals) * 100).toFixed(1) : 0;
            winRateEl.textContent = `${winRate}%`;
        }
    }

    updateCharts() {
        // Update performance chart
        if (this.performanceChart) {
            const newLabel = new Date().toLocaleTimeString();
            this.performanceChart.data.labels.push(newLabel);
            this.performanceChart.data.datasets[0].data.push(this.performanceData.total_profit);
            
            if (this.performanceChart.data.labels.length > 20) {
                this.performanceChart.data.labels.shift();
                this.performanceChart.data.datasets[0].data.shift();
            }
            
            this.performanceChart.update('none');
        }

        // Update distribution chart for PocketOption (CALL/PUT/HOLD)
        if (this.distributionChart) {
            const callSignals = this.signals.filter(s => s.direction === 'CALL').length;
            const putSignals = this.signals.filter(s => s.direction === 'PUT').length;
            const holdSignals = this.signals.filter(s => s.direction === 'HOLD').length;
            
            this.distributionChart.data.datasets[0].data = [callSignals, putSignals, holdSignals];
            this.distributionChart.update('none');
        }
    }

    addSignalToUI(signal) {
        const signalsContainer = document.getElementById('signals-container');
        if (!signalsContainer) return;

        const signalElement = this.createSignalElement(signal);
        
        signalsContainer.insertBefore(signalElement, signalsContainer.firstChild);
        
        // Keep only last 20 signals visible
        if (signalsContainer.children.length > 20) {
            signalsContainer.removeChild(signalsContainer.lastChild);
        }
        
        this.updateLastUpdateTime();
    }

    createSignalElement(signal) {
        const div = document.createElement('div');
        div.className = `signal new-signal`;
        div.innerHTML = `
            <div>${new Date(signal.timestamp).toLocaleTimeString()}</div>
            <div>${signal.asset}</div>
            <div class="${signal.direction.toLowerCase()}">${signal.direction}</div>
            <div>${signal.timeframe}</div>
            <div>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${signal.confidence}%"></div>
                    <div class="confidence-text">${signal.confidence}%</div>
                </div>
            </div>
        `;
        
        // Remove animation class after animation completes
        setTimeout(() => {
            div.classList.remove('new-signal');
        }, 500);
        
        return div;
    }

    displaySignals(signals) {
        const container = document.getElementById('signals-container');
        if (!container) return;
        
        container.innerHTML = '';
        
        signals.forEach(signal => {
            const signalElement = this.createSignalElement(signal);
            container.appendChild(signalElement);
        });
    }

    filterSignals(asset) {
        const filtered = asset === 'all' ? 
            this.signals : 
            this.signals.filter(s => s.asset === asset);
        
        this.displaySignals(filtered);
    }

    searchSignals(query) {
        const filtered = this.signals.filter(s => 
            s.asset.toLowerCase().includes(query.toLowerCase()) ||
            s.direction.toLowerCase().includes(query.toLowerCase()) ||
            s.timeframe.includes(query)
        );
        
        this.displaySignals(filtered);
    }

    updateLastUpdateTime() {
        const lastUpdateEl = document.getElementById('last-update');
        if (lastUpdateEl) {
            lastUpdateEl.textContent = new Date().toLocaleTimeString();
        }
    }

    showNotification(message, type = 'success') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification-badge`;
        notification.textContent = message;
        notification.style.background = type === 'error' ? '#e74c3c' : '#27ae60';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '12px 24px';
        notification.style.borderRadius = '25px';
        notification.style.color = 'white';
        notification.style.fontWeight = 'bold';
        notification.style.zIndex = '1000';
        notification.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page
    if (document.getElementById('signals-container')) {
        window.pocketOptionDashboard = new PocketOptionDashboard();
    }
});

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PocketOptionDashboard;
    }
