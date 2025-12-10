#!/usr/bin/env python3
"""
Script to fix duplicate Flask routes by commenting them out
"""

def fix_duplicates():
    with open('app.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Lines to comment out (0-indexed)
    lines_to_comment = [
        1350,  # @app.route('/api/inventory/summary', methods=['GET']) - second duplicate
        1351,  # def get_inventory_summary(): - second duplicate  
        1386,  # @app.route('/api/inventory/summary', methods=['GET']) - third duplicate
        1387,  # def get_inventory_summary(): - third duplicate
    ]
    
    # Comment out the specified lines
    for line_num in lines_to_comment:
        if line_num < len(lines):
            if lines[line_num].strip().startswith('@app.route') or lines[line_num].strip().startswith('def get_inventory_summary'):
                lines[line_num] = '# ' + lines[line_num]
                print(f"Commented out line {line_num + 1}: {lines[line_num].strip()}")
    
    # Write back to file
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Fixed duplicate routes!")

if __name__ == "__main__":
    fix_duplicates()