#!/usr/bin/env python3
import os
import re

def fix_js_files():
    """Find and fix incorrect API endpoints in JS files"""
    js_dir = "static/js"
    
    # Patterns to fix
    patterns = {
        r"fetch\('/system/status'\)": "fetch('/api/system/status')",
        r"fetch\('/config'\)": "fetch('/api/system/config')",
        r"fetch\('/tasks/active'\)": "fetch('/api/tasks/active')",
        r"'/system/status'": "'/api/system/status'",
        r"'/config'": "'/api/system/config'",
        r"'/tasks/active'": "'/api/tasks/active'",
        r'"/system/status"': '"/api/system/status"',
        r'"/config"': '"/api/system/config"',
        r'"/tasks/active"': '"/api/tasks/active"',
    }
    
    for filename in os.listdir(js_dir):
        if filename.endswith('.js'):
            filepath = os.path.join(js_dir, filename)
            with open(filepath, 'r') as f:
                content = f.read()
            
            original = content
            for pattern, replacement in patterns.items():
                content = re.sub(pattern, replacement, content)
            
            if content != original:
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"Fixed {filename}")
            else:
                print(f"No changes needed for {filename}")

if __name__ == "__main__":
    fix_js_files()
