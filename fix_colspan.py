content = open('templates/sales_management_wine.html', 'r', encoding='utf-8').read()
content = content.replace('colspan="7"', 'colspan="9"')
open('templates/sales_management_wine.html', 'w', encoding='utf-8').write(content)
print('Updated colspan from 7 to 9')
