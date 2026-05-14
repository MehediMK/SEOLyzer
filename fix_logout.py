"""Fix logout links in base.html - targets the exact indented pattern."""
import re

with open('templates/base.html', 'rb') as f:
    content = f.read().decode('utf-8')

# Replace any <a> tag containing logout icon with a form+button
old_pattern = r'(<li>[\r\n\s]+<a[^>]+href="#"[^>]*>[\r\n\s]+<span[^>]+>logout</span>[\r\n\s]+Logout[\r\n\s]+</a>[\r\n\s]+</li>)'

def make_logout_form(m):
    # Detect leading whitespace from the original <li>
    orig = m.group(0)
    # Find the indent of <li>
    indent_match = re.search(r'\n(\s+)<li>', orig)
    indent = indent_match.group(1) if indent_match else '                        '
    inner = indent + '    '
    return (
        f'<li>\n'
        f'{inner}<form method="POST" action="{{% url \'logout\' %}}">\n'
        f'{inner}    {{% csrf_token %}}\n'
        f'{inner}    <button type="submit" class="w-full text-left text-gray-600 hover:text-indigo-600 hover:bg-gray-50 group flex gap-x-3 rounded-md p-2 text-sm font-medium">\n'
        f'{inner}        <span class="material-symbols-outlined">logout</span>\n'
        f'{inner}        Logout\n'
        f'{inner}    </button>\n'
        f'{inner}</form>\n'
        f'{indent}</li>'
    )

new_content, n = re.subn(old_pattern, make_logout_form, content, flags=re.DOTALL)
print(f'Replaced {n} logout link(s)')

with open('templates/base.html', 'wb') as f:
    f.write(new_content.encode('utf-8'))
print('Done.')
