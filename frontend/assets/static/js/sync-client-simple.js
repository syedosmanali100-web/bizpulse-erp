/**
 * Simple Sync Client - REST API Based (No SocketIO)
 * Polls the server for updates instead of WebSocket connection
 */

class SimpleSyncClient {
    constructor() {
        this.connected = false;
        this.polling = false;
        this.pollInterval = null;
        this.lastSyncTime = null;
        this.callbacks = {};
        this.pollFrequency = 30000; // Poll every 30 seconds
        
        console.log('🔄 Simple Sync Client initialized (REST API mode)');
        this.init();
    }
    
    init() {
        // Start polling
        this.startPolling();
        
        // Mark as connected (REST API is always "connected")
        this.connected = true;
        this.emit('connected');
        
        // Do initial sync
        this.requestSync(false);
    }
    
    startPolling() {
        if (this.polling) return;
        
        this.polling = true;
        console.log('🔄 Starting sync polling...');
        
        // Poll immediately
        this.poll();
        
        // Then poll at intervals
        this.pollInterval = setInterval(() => {
            this.poll();
        }, this.pollFrequency);
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.polling = false;
        console.log('⏸️ Sync polling stopped');
    }
    
    async poll() {
        try {
            // Check sync status
            const response = await fetch('/api/sync/status');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.connected = true;
                    this.emit('status_updated', data.data);
                }
            }
        } catch (error) {
            console.error('❌ Sync poll error:', error);
            this.connected = false;
        }
    }
    
    async requestSync(force = false) {
        try {
            console.log('🔄 Requesting sync...');
            
            const response = await fetch('/api/sync/latest-data');
            if (!response.ok) {
                throw new Error('Sync request failed');
            }
            
            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Sync completed successfully');
                this.lastSyncTime = new Date().toISOString();
                
                // Emit sync events for each data type
                const data = result.data;
                
                if (data.products) {
                    this.emit('products_synced', data.products);
                }
                
                if (data.sales) {
                    this.emit('sales_synced', data.sales);
                }
                
                if (data.customers) {
                    this.emit('customers_synced', data.customers);
                }
                
                if (data.invoices) {
                    this.emit('invoices_synced', data.invoices);
                }
                
                this.emit('initial_sync_complete', data);
                
                return true;
            } else {
                console.error('❌ Sync failed:', result.message);
                return false;
            }
            
        } catch (error) {
            console.error('❌ Sync error:', error);
            this.connected = false;
            return false;
        }
    }
    
    on(event, callback) {
        if (!this.callbacks[event]) {
            this.callbacks[event] = [];
        }
        this.callbacks[event].push(callback);
    }
    
    emit(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} callback:`, error);
                }
            });
        }
    }
    
    getStatus() {
        return {
            connected: this.connected,
            polling: this.polling,
            lastSync: this.lastSyncTime
        };
    }
    
    onDataChange(eventType, recordData, tableName) {
        // Notify about data change
        this.emit('data_changed', {
            event_type: eventType,
            table: tableName,
            record: recordData
        });
        
        // Request sync after data change
        setTimeout(() => {
            this.requestSync(false);
        }, 1000);
    }
    
    disconnect() {
        this.stopPolling();
        this.connected = false;
        this.emit('disconnected');
    }
}

// Create global instance
window.syncClient = new SimpleSyncClient();

console.log('✅ Simple Sync Client loaded');
