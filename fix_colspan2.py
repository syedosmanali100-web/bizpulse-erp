content = open('templates/sales_management_wine.html', 'r', encoding='utf-8').read()
content = content.replace('colspan="9"', 'colspan="10"')
open('templates/sales_management_wine.html', 'w', encoding='utf-8').write(content)
print('Updated colspan to 10')
