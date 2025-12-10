import shutil
from datetime import datetime

# Create fresh backup
backup = f'mobile_broken_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
shutil.copy('templates/mobile_web_app.html', backup)
print(f'Backup created: {backup}')

# Copy from the oldest working backup
shutil.copy('mobile_backup_20251207_203654/mobile_web_app.html', 'templates/mobile_web_app.html')
print('Restored from oldest backup')

# Also update mobile_erp_working.html
shutil.copy('mobile_backup_20251207_203654/mobile_erp_working.html', 'templates/mobile_erp_working.html')
print('Updated mobile_erp_working.html')

print('\n✅ DONE! Now restart server and test')
print('Open: http://localhost:5000/mobile')
