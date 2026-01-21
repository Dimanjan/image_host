"""
Script to fix all f-string SQL queries in store_helpers.py
"""

import re

# Read the file
with open("images/store_helpers.py", "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]

    # Check if this is an f-string SQL query
    if 'cursor.execute(f"' in line or "cursor.execute(f'" in line:
        # Find the full statement (might span multiple lines)
        full_stmt = line
        j = i + 1
        while j < len(lines) and (
            full_stmt.count("(") > full_stmt.count(")") or full_stmt.count('"') % 2 != 0
        ):
            full_stmt += lines[j]
            j += 1

        # Extract the SQL and params
        match = re.search(
            r'cursor\.execute\(f["\']([^"\']*)\{([^\}]+)\}([^"\']*)["\'],\s*([^\)]+)\)',
            full_stmt,
        )
        if match:
            before = match.group(1)
            var = match.group(2)
            after = match.group(3)
            params = match.group(4).strip()

            # Create new format
            sql_line = f'                sql = "{before}{{}}{after}".format({var})'
            exec_line = f"                cursor.execute(sql, {params})"

            # Add proper indentation
            indent = len(line) - len(line.lstrip())
            sql_line = " " * indent + sql_line.lstrip()
            exec_line = " " * indent + exec_line.lstrip()

            new_lines.append(sql_line + "\n")
            new_lines.append(exec_line + "\n")
            i = j
            continue

    new_lines.append(line)
    i += 1

# Write back
with open("images/store_helpers.py", "w") as f:
    f.writelines(new_lines)

print("Fixed SQL queries")
