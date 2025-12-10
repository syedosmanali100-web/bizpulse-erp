#!/usr/bin/env python3
"""
Create a clean, working mobile ERP from scratch
"""

# Read the backup
with open('mobile_backup_20251207_203654/mobile_web_app.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove any minified inline scripts and replace with clean version
clean_init_script = '''<script>
// Clean initialization - NO MINIFICATION
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 Mobile ERP Loading...');
    
    // Hide loader after 1.5 seconds
    setTimeout(function() {
        const loader = document.getElementById('mobileLoader');
        if (loader) {
            loader.style.display = 'none';
            console.log('✅ Loader hidden');
        }
        
        // Show login screen
        const loginScreen = document.getElementById('loginScreen');
        if (loginScreen) {
            loginScreen.style.display = 'flex';
            console.log('✅ Login screen shown');
        }
    }, 1500);
    
    // Hide all other screens initially
    document.querySelectorAll('.screen').forEach(function(screen) {
        if (screen.id !== 'loginScreen') {
            screen.style.display = 'none';
        }
    });
    
    // Initialize side menu as closed
    const sideMenu = document.getElementById('sideMenu');
    if (sideMenu) {
        sideMenu.style.left = '-300px';
    }
    
    const overlay = document.getElementById('menuOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
    
    console.log('✅ Mobile ERP initialized');
});

// Login function
function handleLogin() {
    console.log('🔐 Login attempt...');
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (email === 'bizpulse.erp@gmail.com' && password === 'demo123') {
        console.log('✅ Login successful');
        
        // Hide login screen
        document.getElementById('loginScreen').style.display = 'none';
        
        // Show top bar and nav bar
        document.getElementById('topBar').classList.add('show');
        document.getElementById('navBar').classList.add('show');
        
        // Show dashboard
        const dashboard = document.getElementById('dashboardScreen');
        dashboard.classList.add('active');
        dashboard.style.display = 'block';
        
        // Load data after a short delay
        setTimeout(function() {
            if (typeof showScreen === 'function') {
                showScreen('dashboard');
            }
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
            if (typeof loadERPModules === 'function') {
                loadERPModules();
            }
        }, 100);
    } else {
        alert('❌ Wrong credentials!');
    }
}
</script>'''

# Find and replace the minified script
import re
pattern = r'<script>\s*!function\(\)\{.*?\};\s*</script>'
content = re.sub(pattern, clean_init_script, content, flags=re.DOTALL)

# Write the clean version
with open('templates/mobile_web_app.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Clean mobile ERP created!')
print('\n📱 Changes:')
print('   - Removed minified code')
print('   - Added clear console logs')
print('   - Clean, readable JavaScript')
print('\n🚀 Now:')
print('   1. Restart server')
print('   2. Open http://localhost:5000/mobile')
print('   3. Check console (F12) for logs')
print('   4. Login and test hamburger menu')
