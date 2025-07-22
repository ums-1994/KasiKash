import re

with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the referral route
start = None
end = None
for i, line in enumerate(lines):
    if re.match(r"^\s*@app\.route\(['\"]\/referral['\"]", line):
        start = i
        # Find the end of the function (next unindented line or EOF)
        for j in range(i+1, len(lines)):
            if lines[j].startswith("@app.route") or lines[j].startswith("if __name__ == \"__main__\""):
                end = j
                break
        else:
            end = len(lines)
        break

if start is None or end is None:
    print("Could not find /referral route in main.py")
    exit(1)

referral_block = lines[start:end]
# Remove the referral block from its current location
lines = lines[:start] + lines[end:]

# Find the last if __name__ == "__main__": block
for i, line in enumerate(lines):
    if line.strip().startswith('if __name__ == "__main__"'):
        insert_at = i
        break
else:
    print("Could not find if __name__ == \"__main__\": block in main.py")
    exit(1)

# Insert the referral block just before the if __name__ == "__main__": block
lines = lines[:insert_at] + referral_block + ["\n"] + lines[insert_at:]

with open("main.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Referral route moved successfully!")