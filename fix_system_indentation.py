#!/usr/bin/env python3
import re

with open("app/api/system.py", "r") as f:
    lines = f.readlines()

# Find the update_model function
in_update_model = False
fixed_lines = []

for i, line in enumerate(lines):
    # Look for the update_model function
    if 'async def update_model' in line:
        in_update_model = True
        print(f"Found update_model function at line {i+1}")
    
    # Fix indentation within update_model
    if in_update_model:
        # Check if this line has wrong indentation
        stripped = line.lstrip()
        if stripped.startswith('raise HTTPException'):
            # Should be indented 8 spaces (2 tabs) inside the try block
            if not line.startswith(' ' * 8):
                line = ' ' * 8 + stripped
                print(f"Fixed indentation at line {i+1}")
    
    # Check for end of function
    if in_update_model and line.strip() == '' and i > 0:
        # Check if previous line ends the function
        prev_line = lines[i-1].strip()
        if prev_line.startswith('return') or prev_line.startswith('}'):
            in_update_model = False
    
    fixed_lines.append(line)

# Write back
with open("app/api/system.py", "w") as f:
    f.writelines(fixed_lines)

print("Fixed indentation in system.py")
