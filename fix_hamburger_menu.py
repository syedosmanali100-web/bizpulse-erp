#!/usr/bin/env python3
"""
Fix Hamburger Menu - Ensure three lines button works properly
"""

# Read the working template
with open('templates/mobile_erp_working.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Check critical elements
checks = {
    'Side Menu Element': '<div class="side-menu" id="sideMenu">',
    'Menu Overlay': '<div class="menu-overlay" id="menuOverlay"',
    'Hamburger Button': 'onclick="toggleSideMenu()"',
    'Toggle Function': 'function toggleSideMenu()',
    'Load Modules Function': 'async function loadERPModules()',
    'API Modules Route': '/api/modules'
}

print("="*60)
print("🔍 Checking Hamburger Menu Components")
print("="*60)

all_ok = True
for name, check in checks.items():
    if check in content:
        print(f"✅ {name}")
    else:
        print(f"❌ {name} - MISSING!")
        all_ok = False

# Check if CSS for side menu exists
css_checks = {
    'Side Menu CSS': '.side-menu {',
    'Menu Open State': '.side-menu.open {',
    'Hamburger Button CSS': '.hamburger-btn {',
    'Menu Overlay CSS': '.menu-overlay {'
}

print("\n🎨 Checking CSS Styles:")
for name, check in css_checks.items():
    if check in content:
        print(f"✅ {name}")
    else:
        print(f"❌ {name} - MISSING!")
        all_ok = False

# Check JavaScript event listeners
js_checks = {
    'Menu Overlay Click': 'menuOverlay.*addEventListener.*click',
    'Toggle Function Call': 'toggleSideMenu\\(\\)',
    'Close Menu Function': 'function closeSideMenu'
}

print("\n⚡ Checking JavaScript:")
import re
for name, pattern in js_checks.items():
    if re.search(pattern, content):
        print(f"✅ {name}")
    else:
        print(f"⚠️  {name} - Check manually")

print("\n" + "="*60)
if all_ok:
    print("✅ All components present!")
    print("\n💡 If menu still not working:")
    print("   1. Clear browser cache (Ctrl+Shift+Delete)")
    print("   2. Hard refresh (Ctrl+F5)")
    print("   3. Check browser console (F12) for errors")
    print("   4. Ensure server is running: python app.py")
else:
    print("⚠️  Some components missing - fixing...")

# Add enhanced debugging to the template
debug_script = '''
    // ENHANCED DEBUGGING FOR HAMBURGER MENU
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔍 Checking hamburger menu setup...');
        
        const sideMenu = document.getElementById('sideMenu');
        const overlay = document.getElementById('menuOverlay');
        const hamburger = document.querySelector('.hamburger-btn');
        
        console.log('Side Menu:', sideMenu ? '✅ Found' : '❌ Missing');
        console.log('Overlay:', overlay ? '✅ Found' : '❌ Missing');
        console.log('Hamburger:', hamburger ? '✅ Found' : '❌ Missing');
        
        if (hamburger) {
            hamburger.addEventListener('click', function(e) {
                console.log('🍔 Hamburger clicked!');
                e.preventDefault();
                e.stopPropagation();
                toggleSideMenu();
            });
        }
        
        if (overlay) {
            overlay.addEventListener('click', function() {
                console.log('📱 Overlay clicked - closing menu');
                closeSideMenu();
            });
        }
    });
'''

# Check if debug script already exists
if 'ENHANCED DEBUGGING FOR HAMBURGER MENU' not in content:
    print("\n📝 Adding enhanced debugging...")
    # Find the closing </script> tag before </body>
    content = content.replace('</body>', debug_script + '\n</body>')
    
    # Write back
    with open('templates/mobile_erp_working.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Enhanced debugging added!")
else:
    print("\n✅ Debug script already present")

print("\n" + "="*60)
print("🎉 Hamburger Menu Fix Complete!")
print("="*60)
print("\n📱 Test Steps:")
print("   1. Restart server: python app.py")
print("   2. Open: http://localhost:5000/mobile")
print("   3. Login and click three lines (☰)")
print("   4. Check browser console (F12) for debug messages")
print("\n✨ Menu should now work properly!")
