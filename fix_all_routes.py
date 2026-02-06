#!/usr/bin/env python3
import os

# 1. Fix main.py router prefixes
with open("app/main.py", "r") as f:
    content = f.read()

# Update router prefixes
replacements = [
    ('prefix="/api"', 'prefix="/api/chat"'),
    ('prefix="/api"', 'prefix="/api/files"'),
    ('prefix="/api"', 'prefix="/api/system"'),
    ('prefix="/api"', 'prefix="/api/tasks"'),
]

# Apply replacements
new_content = content
for old, new in replacements:
    new_content = new_content.replace(old, new)

with open("app/main.py", "w") as f:
    f.write(new_content)
print("✅ Fixed main.py router prefixes")

# 2. Fix files.py routes
with open("app/api/files.py", "r") as f:
    content = f.read()

# Update routes
content = content.replace('@router.get("/files")', '@router.get("/")')
content = content.replace('@router.delete("/files/{filename}")', '@router.delete("/{filename}")')

with open("app/api/files.py", "w") as f:
    f.write(content)
print("✅ Fixed files.py routes")

# 3. Fix tasks.py routes  
with open("app/api/tasks.py", "r") as f:
    content = f.read()

# Update routes
content = content.replace('@router.get("/tasks/{task_id}")', '@router.get("/{task_id}")')
content = content.replace('@router.get("/tasks")', '@router.get("/")')

with open("app/api/tasks.py", "w") as f:
    f.write(content)
print("✅ Fixed tasks.py routes")

# 4. Remove duplicate get_config in system.py
with open("app/api/system.py", "r") as f:
    lines = f.readlines()

# Find and remove duplicate get_config (second occurrence)
in_duplicate = False
skip_lines = 0
new_lines = []

for i, line in enumerate(lines):
    if 'async def get_config():' in line:
        if in_duplicate:  # Second occurrence
            skip_lines = 30  # Skip this function (approx 30 lines)
        in_duplicate = True
    
    if skip_lines > 0:
        skip_lines -= 1
        continue
    
    new_lines.append(line)

with open("app/api/system.py", "w") as f:
    f.writelines(new_lines)
print("✅ Removed duplicate get_config in system.py")

print("\n🎉 All fixes applied! Restart your server.")
