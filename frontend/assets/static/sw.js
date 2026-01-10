// BizPulse Service Worker - Offline Support
const CACHE_NAME = 'bizpulse-v1.0.0';
const OFFLINE_URL = '/offline.html';

// Files to cache for offline use
const CACHE_FILES = [
  '/',
  '/retail/dashboard',
  '/retail/billing', 
  '/retail/products',
  '/retail/customers',
  '/static/manifest.json',
  '/offline.html'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
  console.log('🛒 BizPulse Service Worker installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('📦 Caching app files...');
        return cache.addAll(CACHE_FILES);
      })
      .then(() => {
        console.log('✅ BizPulse cached successfully!');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('🚀 BizPulse Service Worker activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('✅ BizPulse Service Worker activated!');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip external requests
  if (!event.request.url.startsWith(self.location.origin)) return;

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version if available
        if (response) {
          console.log('📦 Serving from cache:', event.request.url);
          return response;
        }
        
        // Try to fetch from network
        return fetch(event.request)
          .then((response) => {
            // Don't cache non-successful responses
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone response for caching
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          })
          .catch(() => {
            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

// Background sync for data when back online
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    console.log('🔄 Background sync triggered');
    event.waitUntil(syncData());
  }
});

// Push notification handling
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New update available!',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open BizPulse',
        icon: '/static/icon-192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/icon-192.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('🛒 BizPulse', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Sync data function
async function syncData() {
  try {
    console.log('📡 Background syncing data...');
    
    // Get user info from IndexedDB or localStorage
    const userInfo = await getUserInfo();
    if (!userInfo || !userInfo.id) {
      console.log('❌ No user info for background sync');
      return Promise.resolve();
    }
    
    // Sync latest data
    const response = await fetch('/api/sync/latest-data', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const result = await response.json();
      if (result.success) {
        // Store synced data in IndexedDB for offline access
        await storeOfflineData(result.data);
        console.log('✅ Background sync completed');
        
        // Notify all clients about the sync
        const clients = await self.clients.matchAll();
        clients.forEach(client => {
          client.postMessage({
            type: 'BACKGROUND_SYNC_COMPLETE',
            data: result.data
          });
        });
      }
    }
    
    return Promise.resolve();
  } catch (error) {
    console.error('❌ Background sync failed:', error);
    return Promise.reject(error);
  }
}

// Helper function to get user info
async function getUserInfo() {
  try {
    // Try to get from IndexedDB first, then localStorage
    return new Promise((resolve) => {
      const request = indexedDB.open('BizPulseDB', 1);
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        if (db.objectStoreNames.contains('userInfo')) {
          const transaction = db.transaction(['userInfo'], 'readonly');
          const store = transaction.objectStore('userInfo');
          const getRequest = store.get('current');
          
          getRequest.onsuccess = () => {
            resolve(getRequest.result || null);
          };
          
          getRequest.onerror = () => {
            resolve(null);
          };
        } else {
          resolve(null);
        }
      };
      
      request.onerror = () => {
        resolve(null);
      };
    });
  } catch (error) {
    console.error('❌ Error getting user info:', error);
    return null;
  }
}

// Helper function to store offline data
async function storeOfflineData(data) {
  try {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('BizPulseDB', 1);
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores if they don't exist
        if (!db.objectStoreNames.contains('products')) {
          db.createObjectStore('products', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('sales')) {
          db.createObjectStore('sales', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('customers')) {
          db.createObjectStore('customers', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('invoices')) {
          db.createObjectStore('invoices', { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains('syncMeta')) {
          db.createObjectStore('syncMeta', { keyPath: 'key' });
        }
      };
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        const transaction = db.transaction(['products', 'sales', 'customers', 'invoices', 'syncMeta'], 'readwrite');
        
        // Store each data type
        if (data.products) {
          const productsStore = transaction.objectStore('products');
          data.products.forEach(product => {
            productsStore.put(product);
          });
        }
        
        if (data.sales) {
          const salesStore = transaction.objectStore('sales');
          data.sales.forEach(sale => {
            salesStore.put(sale);
          });
        }
        
        if (data.customers) {
          const customersStore = transaction.objectStore('customers');
          data.customers.forEach(customer => {
            customersStore.put(customer);
          });
        }
        
        if (data.invoices) {
          const invoicesStore = transaction.objectStore('invoices');
          data.invoices.forEach(invoice => {
            invoicesStore.put(invoice);
          });
        }
        
        // Store sync metadata
        const metaStore = transaction.objectStore('syncMeta');
        metaStore.put({
          key: 'lastSync',
          timestamp: data.sync_timestamp || new Date().toISOString()
        });
        
        transaction.oncomplete = () => {
          console.log('✅ Offline data stored successfully');
          resolve();
        };
        
        transaction.onerror = (error) => {
          console.error('❌ Error storing offline data:', error);
          reject(error);
        };
      };
      
      request.onerror = (error) => {
        console.error('❌ Error opening IndexedDB:', error);
        reject(error);
      };
    });
  } catch (error) {
    console.error('❌ Error in storeOfflineData:', error);
    throw error;
  }
}