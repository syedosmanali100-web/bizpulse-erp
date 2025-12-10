// BizPulse Mobile App Configuration
// Update the SERVER_URL with your computer's IP address

const MOBILE_CONFIG = {
    // CHANGE THIS TO YOUR COMPUTER'S IP ADDRESS
    SERVER_URL: 'http://192.168.31.75:5000', // Replace with your actual IP
    
    // Alternative URLs to try (the app will test these automatically)
    FALLBACK_URLS: [
        'http://192.168.1.100:5000',  // Common router IP range
        'http://192.168.0.100:5000',  // Alternative router IP range
        'http://10.0.2.2:5000',       // Android emulator host
        'http://localhost:5000',      // Local development
        'http://127.0.0.1:5000'       // Loopback
    ],
    
    // App settings
    API_BASE: '/api',
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 2000,
    
    // Demo credentials
    DEMO_EMAIL: 'admin@demo.com',
    DEMO_PASSWORD: 'demo123'
};

// How to find your computer's IP address:
// 
// Windows:
// 1. Open Command Prompt (cmd)
// 2. Type: ipconfig
// 3. Look for "IPv4 Address" under your WiFi adapter
// 
// Mac/Linux:
// 1. Open Terminal
// 2. Type: ifconfig or hostname -I
// 3. Look for your network interface IP
//
// Example IPs:
// - 192.168.1.xxx (most common)
// - 192.168.0.xxx (alternative)
// - 10.0.0.xxx (some routers)
//
// Make sure both your computer and phone are on the same WiFi network!