// PWA utilities and offline management
class PWAManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.serviceWorker = null;
    this.offlineQueue = [];
    this.listeners = {
      online: [],
      offline: [],
      beforeinstallprompt: [],
      appinstalled: []
    };
    
    this.init();
  }

  init() {
    // Register service worker
    this.registerServiceWorker();
    
    // Set up online/offline event listeners
    this.setupNetworkListeners();
    
    // Set up PWA install prompt handling
    this.setupInstallPrompt();
    
    // Initialize offline queue from localStorage
    this.loadOfflineQueue();
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        this.serviceWorker = registration;
        
        console.log('Service Worker registered successfully');
        
        // Handle service worker updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // New service worker available, show update notification
              this.showUpdateNotification();
            }
          });
        });
        
        // Listen for messages from service worker
        navigator.serviceWorker.addEventListener('message', (event) => {
          this.handleServiceWorkerMessage(event);
        });
        
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  setupNetworkListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processOfflineQueue();
      this.emit('online');
      this.hideOfflineIndicator();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.emit('offline');
      this.showOfflineIndicator();
    });
  }

  setupInstallPrompt() {
    let deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', (event) => {
      event.preventDefault();
      deferredPrompt = event;
      this.emit('beforeinstallprompt', event);
    });

    window.addEventListener('appinstalled', (event) => {
      console.log('PWA was installed');
      this.emit('appinstalled', event);
    });

    // Make install method available
    this.installApp = async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const result = await deferredPrompt.userChoice;
        deferredPrompt = null;
        return result.outcome === 'accepted';
      }
      return false;
    };
  }

  // Event listener management
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
  }

  off(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback);
      if (index > -1) {
        this.listeners[event].splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  // Offline queue management
  addToOfflineQueue(request) {
    const queueItem = {
      id: Date.now() + Math.random(),
      url: request.url,
      method: request.method,
      headers: request.headers ? Object.fromEntries(request.headers.entries()) : {},
      body: request.body,
      timestamp: Date.now()
    };
    
    this.offlineQueue.push(queueItem);
    this.saveOfflineQueue();
    
    return queueItem.id;
  }

  async processOfflineQueue() {
    if (!this.isOnline || this.offlineQueue.length === 0) {
      return;
    }

    console.log(`Processing ${this.offlineQueue.length} offline requests`);
    
    const results = [];
    
    for (const item of this.offlineQueue) {
      try {
        const response = await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body
        });
        
        results.push({ id: item.id, success: true, response });
        console.log(`Successfully processed offline request: ${item.url}`);
        
      } catch (error) {
        results.push({ id: item.id, success: false, error });
        console.error(`Failed to process offline request: ${item.url}`, error);
      }
    }
    
    // Remove successfully processed items
    this.offlineQueue = this.offlineQueue.filter(item => 
      !results.some(result => result.id === item.id && result.success)
    );
    
    this.saveOfflineQueue();
    
    if (results.some(r => r.success)) {
      this.showToast('Offline changes have been synchronized', 'success');
    }
    
    return results;
  }

  loadOfflineQueue() {
    try {
      const stored = localStorage.getItem('sonicus_offline_queue');
      if (stored) {
        this.offlineQueue = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load offline queue:', error);
      this.offlineQueue = [];
    }
  }

  saveOfflineQueue() {
    try {
      localStorage.setItem('sonicus_offline_queue', JSON.stringify(this.offlineQueue));
    } catch (error) {
      console.error('Failed to save offline queue:', error);
    }
  }

  clearOfflineQueue() {
    this.offlineQueue = [];
    localStorage.removeItem('sonicus_offline_queue');
  }

  // Network-aware fetch wrapper
  async fetch(url, options = {}) {
    if (!this.isOnline) {
      // Add to offline queue and return a promise that resolves when back online
      this.addToOfflineQueue(new Request(url, options));
      
      throw new Error('Offline - Request queued for when connection is restored');
    }

    try {
      const response = await fetch(url, options);
      
      // Cache critical admin data in service worker
      if (response.ok && url.includes('/api/admin/')) {
        this.cacheAdminData(await response.clone().json());
      }
      
      return response;
    } catch (error) {
      // If request fails and we're still online, it might be a temporary network issue
      if (this.isOnline) {
        this.addToOfflineQueue(new Request(url, options));
      }
      throw error;
    }
  }

  // Cache admin data in service worker
  cacheAdminData(data) {
    if (this.serviceWorker && this.serviceWorker.active) {
      this.serviceWorker.active.postMessage({
        type: 'CACHE_ADMIN_DATA',
        data: data
      });
    }
  }

  // UI helpers
  showOfflineIndicator() {
    let indicator = document.getElementById('offline-indicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'offline-indicator';
      indicator.className = 'offline-indicator';
      indicator.innerHTML = `
        <div class="offline-content">
          <span class="offline-icon">📱</span>
          <span class="offline-text">You're offline</span>
          <span class="offline-subtext">Changes will sync when you're back online</span>
        </div>
      `;
      document.body.appendChild(indicator);
    }
    
    indicator.classList.add('show');
  }

  hideOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator');
    if (indicator) {
      indicator.classList.remove('show');
    }
  }

  showUpdateNotification() {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
      <div class="update-content">
        <span class="update-text">A new version is available</span>
        <button class="btn btn-primary btn-sm update-btn">Update</button>
        <button class="btn btn-secondary btn-sm dismiss-btn">Later</button>
      </div>
    `;
    
    notification.querySelector('.update-btn').addEventListener('click', () => {
      this.updateApp();
      notification.remove();
    });
    
    notification.querySelector('.dismiss-btn').addEventListener('click', () => {
      notification.remove();
    });
    
    document.body.appendChild(notification);
  }

  updateApp() {
    if (this.serviceWorker && this.serviceWorker.waiting) {
      this.serviceWorker.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }

  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `mobile-toast ${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;
    
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }

  handleServiceWorkerMessage(event) {
    const { data } = event;
    
    switch (data.type) {
      case 'OFFLINE_DATA_CACHED':
        console.log('Admin data cached for offline use');
        break;
      case 'BACKGROUND_SYNC_COMPLETE':
        this.showToast('Background sync completed', 'success');
        break;
      default:
        console.log('Service worker message:', data);
    }
  }

  // Utility methods
  isPWAInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  canInstallPWA() {
    return !!this.deferredPrompt;
  }

  getNetworkStatus() {
    return {
      online: this.isOnline,
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      } : null,
      offlineQueueLength: this.offlineQueue.length
    };
  }

  // Performance monitoring
  measurePerformance(name, fn) {
    return async (...args) => {
      const start = performance.now();
      try {
        const result = await fn.apply(this, args);
        const end = performance.now();
        console.log(`Performance: ${name} took ${end - start} milliseconds`);
        return result;
      } catch (error) {
        const end = performance.now();
        console.log(`Performance: ${name} failed after ${end - start} milliseconds`);
        throw error;
      }
    };
  }
}

// Create global PWA manager instance
const pwaManager = new PWAManager();

// Export for use in components
export default pwaManager;

// Also make it available globally for debugging
if (typeof window !== 'undefined') {
  window.pwaManager = pwaManager;
}
