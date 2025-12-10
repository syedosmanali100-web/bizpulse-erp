#!/usr/bin/env python3
# Script to delete modular section from index.html

with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line numbers
css_start = None
css_end = None
html_start = None
html_end = None
js_start = None

for i, line in enumerate(lines):
    if '/* ========= SIMPLE MODULAR SECTION ========= */' in line:
        css_start = i
    elif '/* Products Section */' in line and css_start:
        css_end = i
    elif '<!-- ========= SIMPLE BOXES SECTION ========= -->' in line:
        html_start = i
    elif '<!-- Stats Section -->' in line and html_start:
        html_end = i
    elif '// ========= JS : CATEGORY-WISE ANIMATION WITH LINES =========' in line:
        js_start = i

print(f"CSS: lines {css_start} to {css_end}")
print(f"HTML: lines {html_start} to {html_end}")
print(f"JS: line {js_start} onwards")

# Delete sections
new_lines = []

# Keep everything before CSS section
new_lines.extend(lines[:css_start])

# Add empty space marker for CSS
new_lines.append('\n        /* ========= MODULAR SECTION - EMPTY ========= */\n\n')

# Keep from CSS end to HTML start
new_lines.extend(lines[css_end:html_start])

# Add empty space marker for HTML
new_lines.append('\n    <!-- ========= MODULAR SECTION - EMPTY ========= -->\n\n')

# Keep from HTML end to JS start
new_lines.extend(lines[html_end:js_start])

# Add empty space marker for JS
new_lines.append('\n        // ========= MODULAR SECTION JS - EMPTY =========\n\n')

# Keep rest after JS (closing tags)
# Find the closing of the IIFE function
for i in range(js_start, len(lines)):
    if 'animateCategory();' in lines[i]:
        # Skip to end of this function
        for j in range(i, len(lines)):
            if lines[j].strip() == '})();':
                new_lines.extend(lines[j+1:])
                break
        break

# Write back
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Deleted all modular section code!")
print("✅ Left empty space markers")
