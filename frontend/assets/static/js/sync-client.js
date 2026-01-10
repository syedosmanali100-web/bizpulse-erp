/**
 * Real-time Sync Client
 * Handles WebSocket connections and data synchronization across devices
 */

class SyncClient {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.lastSyncTimestamp = null;
        this.syncCallbacks = {};
        this.deviceId = this.generateDeviceId();
        
        // Bind methods
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.onDataChange = this.onDataChange.bind(this);
        this.requestSync = this.requestSync.bind(this);
    }
    
    generateDeviceId() {
        // Generate unique device ID
        let deviceId = localStorage.getItem('bizpulse_device_id');
        if (!deviceId) {
            deviceId = 'device_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('bizpulse_device_id', deviceId);
        }
        return deviceId;
    }
    
    connect(userId) {
        if (this.isConnected || !userId) {
            return;
        }
        
        try {
            // Load Socket.IO from CDN if not already loaded
            if (typeof io === 'undefined') {
                this.loadSocketIO(() => this.initializeConnection(userId));
                return;
            }
            
            this.initializeConnection(userId);
            
        } catch (error) {
            console.error('❌ Sync connection error:', error);
            this.scheduleReconnect(userId);
        }
    }
    
    loadSocketIO(callback) {
        const script = document.createElement('script');
        script.src = 'https://cdn.socket.io/4.7.2/socket.io.min.js';
        script.onload = callback;
        script.onerror = () => {
            console.error('❌ Failed to load Socket.IO');
            // Fallback to polling-based sync
            this.enablePollingSync();
        };
        document.head.appendChild(script);
    }
    
    initializeConnection(userId) {
        const platform = this.detectPlatform();
        
        this.socket = io({
            query: {
                user_id: userId,
                platform: platform,
                device_id: this.deviceId
            },
            transports: ['websocket', 'polling'],
            timeout: 10000,
            forceNew: true
        });
        
        this.setupEventHandlers(userId);
    }
    
    setupEventHandlers(userId) {
        // Connection events
        this.socket.on('connect', () => {
            console.log('✅ Sync connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this.showSyncStatus('Connected', 'success');
            
            // Start heartbeat
            this.startHeartbeat();
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('❌ Sync disconnected:', reason);
            this.isConnected = false;
            this.showSyncStatus('Disconnected', 'error');
            
            // Auto-reconnect unless manually disconnected
            if (reason !== 'io client disconnect') {
                this.scheduleReconnect(userId);
            }
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('❌ Sync connection error:', error);
            this.isConnected = false;
            this.showSyncStatus('Connection Error', 'error');
            this.scheduleReconnect(userId);
        });
        
        // Sync events
        this.socket.on('initial_sync', (data) => {
            console.log('📡 Initial sync received:', data);
            if (data.success && data.data) {
                this.lastSyncTimestamp = data.data.sync_timestamp;
                this.handleInitialSync(data.data);
                this.showSyncStatus('Synced', 'success');
            }
        });
        
        this.socket.on('data_sync', (data) => {
            console.log('🔄 Data sync received:', data);
            this.handleDataSync(data);
        });
        
        this.socket.on('force_sync', (data) => {
            console.log('⚡ Force sync received:', data);
            this.handleForceSync(data);
        });
        
        this.socket.on('device_connected', (data) => {
            console.log('📱 New device connected:', data);
            this.showSyncNotification('New device connected', 'info');
        });
        
        this.socket.on('device_disconnected', (data) => {
            console.log('📱 Device disconnected:', data);
        });
        
        this.socket.on('sync_error', (data) => {
            console.error('❌ Sync error:', data);
            this.showSyncStatus('Sync Error', 'error');
        });
        
        this.socket.on('pong', (data) => {
            // Heartbeat response
            this.lastSyncTimestamp = data.timestamp;
        });
    }
    
    scheduleReconnect(userId) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ Max reconnection attempts reached. Switching to polling sync.');
            this.enablePollingSync();
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
        
        console.log(`🔄 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect(userId);
        }, delay);
    }
    
    startHeartbeat() {
        // Send ping every 30 seconds to keep connection alive
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected && this.socket) {
                this.socket.emit('ping');
            }
        }, 30000);
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        this.isConnected = false;
        console.log('✅ Sync disconnected');
    }
    
    // Data change notification (called when local data changes)
    onDataChange(eventType, data, tableName) {
        if (!this.isConnected || !this.socket) {
            // Queue for later sync
            this.queueDataChange(eventType, data, tableName);
            return;
        }
        
        this.socket.emit('data_changed', {
            event_type: eventType,
            data: {
                table: tableName,
                record: data,
                timestamp: new Date().toISOString()
            }
        });
        
        console.log(`📤 Data change sent: ${eventType} on ${tableName}`);
    }
    
    // Request manual sync
    requestSync(includeFullData = false) {
        if (!this.isConnected || !this.socket) {
            // Fallback to REST API
            this.requestSyncViaAPI(includeFullData);
            return;
        }
        
        this.socket.emit('request_sync', {
            since_timestamp: this.lastSyncTimestamp,
            include_full_data: includeFullData
        });
        
        console.log('📡 Manual sync requested');
        this.showSyncStatus('Syncing...', 'info');
    }
    
    // Handle sync events
    handleInitialSync(data) {
        // Update local data with server data
        if (data.products) {
            this.triggerCallback('products_synced', data.products);
        }
        if (data.sales) {
            this.triggerCallback('sales_synced', data.sales);
        }
        if (data.customers) {
            this.triggerCallback('customers_synced', data.customers);
        }
        if (data.invoices) {
            this.triggerCallback('invoices_synced', data.invoices);
        }
        
        this.triggerCallback('initial_sync_complete', data);
    }
    
    handleDataSync(data) {
        const event = data.event;
        const sourceSession = data.source_session;
        
        // Don't process events from this device
        if (sourceSession === this.socket?.id) {
            return;
        }
        
        // Process the sync event
        this.triggerCallback('data_changed', {
            event_type: event.event_type,
            table: event.data.table,
            record: event.data.record,
            timestamp: event.timestamp
        });
        
        this.showSyncNotification(`Data ${event.event_type}d on another device`, 'info');
    }
    
    handleForceSync(data) {
        this.lastSyncTimestamp = data.timestamp;
        this.handleInitialSync(data.latest_data);
        this.showSyncNotification('Data force synced', 'success');
    }
    
    // Fallback polling sync (when WebSocket fails)
    enablePollingSync() {
        console.log('🔄 Enabling polling sync fallback');
        this.showSyncStatus('Polling Mode', 'warning');
        
        // Poll every 30 seconds
        this.pollingInterval = setInterval(() => {
            this.requestSyncViaAPI(false);
        }, 30000);
    }
    
    async requestSyncViaAPI(includeFullData = false) {
        try {
            const response = await fetch('/api/sync/latest-data');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.handleInitialSync(result.data);
                    this.showSyncStatus('Synced (API)', 'success');
                }
            }
        } catch (error) {
            console.error('❌ API sync error:', error);
            this.showSyncStatus('Sync Failed', 'error');
        }
    }
    
    // Queue data changes when offline
    queueDataChange(eventType, data, tableName) {
        let queue = JSON.parse(localStorage.getItem('sync_queue') || '[]');
        queue.push({
            event_type: eventType,
            data: { table: tableName, record: data },
            timestamp: new Date().toISOString(),
            queued: true
        });
        
        // Keep only last 50 items
        if (queue.length > 50) {
            queue = queue.slice(-50);
        }
        
        localStorage.setItem('sync_queue', JSON.stringify(queue));
        console.log('📦 Data change queued for later sync');
    }
    
    // Process queued changes when back online
    processQueuedChanges() {
        const queue = JSON.parse(localStorage.getItem('sync_queue') || '[]');
        if (queue.length === 0) return;
        
        console.log(`📤 Processing ${queue.length} queued changes`);
        
        queue.forEach(change => {
            this.onDataChange(change.event_type, change.data.record, change.data.table);
        });
        
        // Clear queue
        localStorage.removeItem('sync_queue');
    }
    
    // Callback system
    on(event, callback) {
        if (!this.syncCallbacks[event]) {
            this.syncCallbacks[event] = [];
        }
        this.syncCallbacks[event].push(callback);
    }
    
    off(event, callback) {
        if (this.syncCallbacks[event]) {
            this.syncCallbacks[event] = this.syncCallbacks[event].filter(cb => cb !== callback);
        }
    }
    
    triggerCallback(event, data) {
        if (this.syncCallbacks[event]) {
            this.syncCallbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ Callback error for ${event}:`, error);
                }
            });
        }
    }
    
    // UI helpers
    showSyncStatus(message, type = 'info') {
        // Create or update sync status indicator
        let indicator = document.getElementById('sync-status-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'sync-status-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 500;
                z-index: 10000;
                transition: all 0.3s ease;
                pointer-events: none;
            `;
            document.body.appendChild(indicator);
        }
        
        const colors = {
            success: '#10B981',
            error: '#EF4444',
            warning: '#F59E0B',
            info: '#3B82F6'
        };
        
        indicator.textContent = `🔄 ${message}`;
        indicator.style.backgroundColor = colors[type] || colors.info;
        indicator.style.color = 'white';
        indicator.style.opacity = '1';
        
        // Auto-hide after 3 seconds for non-error messages
        if (type !== 'error') {
            setTimeout(() => {
                indicator.style.opacity = '0.7';
            }, 3000);
        }
    }
    
    showSyncNotification(message, type = 'info') {
        // Show temporary notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 50px;
            right: 10px;
            padding: 12px 16px;
            background: #1F2937;
            color: white;
            border-radius: 8px;
            font-size: 14px;
            z-index: 10001;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 4 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 4000);
    }
    
    detectPlatform() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (userAgent.includes('mobile') || userAgent.includes('android') || userAgent.includes('iphone')) {
            return 'mobile';
        } else if (userAgent.includes('tablet') || userAgent.includes('ipad')) {
            return 'tablet';
        }
        return 'desktop';
    }
    
    // Public API
    getStatus() {
        return {
            connected: this.isConnected,
            deviceId: this.deviceId,
            lastSync: this.lastSyncTimestamp,
            reconnectAttempts: this.reconnectAttempts
        };
    }
}

// Global sync client instance
window.syncClient = new SyncClient();

// Auto-connect when user info is available
document.addEventListener('DOMContentLoaded', () => {
    // Try to get user info and connect
    const userInfo = localStorage.getItem('userInfo');
    if (userInfo) {
        try {
            const user = JSON.parse(userInfo);
            if (user.id) {
                console.log('🚀 Auto-connecting sync client for user:', user.id);
                window.syncClient.connect(user.id);
            }
        } catch (error) {
            console.error('❌ Failed to parse user info:', error);
        }
    }
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.syncClient.isConnected) {
        // Request sync when page becomes visible
        window.syncClient.requestSync();
    }
});

// Handle online/offline events
window.addEventListener('online', () => {
    console.log('🌐 Back online - reconnecting sync');
    const userInfo = localStorage.getItem('userInfo');
    if (userInfo) {
        const user = JSON.parse(userInfo);
        window.syncClient.connect(user.id);
    }
});

window.addEventListener('offline', () => {
    console.log('📴 Gone offline - sync will queue changes');
    window.syncClient.showSyncStatus('Offline', 'warning');
});