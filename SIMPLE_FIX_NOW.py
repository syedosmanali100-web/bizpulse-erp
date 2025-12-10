#!/usr/bin/env python3
"""
SIMPLE FIX - Just make hamburger menu work RIGHT NOW
"""

with open('templates/mobile_web_app.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Add a simple fix script right after body tag
fix_script = '''
<script>
// IMMEDIATE FIX FOR HAMBURGER MENU
window.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Applying hamburger fix...');
    
    // Get elements
    const hamburger = document.querySelector('.hamburger-btn');
    const sideMenu = document.getElementById('sideMenu');
    const overlay = document.getElementById('menuOverlay');
    
    console.log('Hamburger:', hamburger ? '✅' : '❌');
    console.log('Side Menu:', sideMenu ? '✅' : '❌');
    console.log('Overlay:', overlay ? '✅' : '❌');
    
    // Force add click listener
    if (hamburger) {
        hamburger.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🍔 HAMBURGER CLICKED!');
            
            if (sideMenu && overlay) {
                if (sideMenu.classList.contains('open')) {
                    sideMenu.classList.remove('open');
                    overlay.classList.remove('show');
                } else {
                    sideMenu.classList.add('open');
                    overlay.classList.add('show');
                    
                    // Load modules
                    if (typeof loadERPModules === 'function') {
                        loadERPModules();
                    }
                }
            }
        };
        console.log('✅ Hamburger click handler added!');
    }
    
    // Overlay click to close
    if (overlay) {
        overlay.onclick = function() {
            if (sideMenu) sideMenu.classList.remove('open');
            overlay.classList.remove('show');
        };
    }
});
</script>
'''

# Check if fix already exists
if '// IMMEDIATE FIX FOR HAMBURGER MENU' not in content:
    # Add right after <body> tag
    content = content.replace('<body>', '<body>\n' + fix_script)
    
    with open('templates/mobile_web_app.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ FIX APPLIED!")
    print("\n🚀 Now:")
    print("   1. Restart server: python app.py")
    print("   2. Open: http://localhost:5000/mobile")
    print("   3. Login and click hamburger (☰)")
    print("\n✨ Should work now!")
else:
    print("✅ Fix already applied!")
    print("\n📱 Just restart server and test")
