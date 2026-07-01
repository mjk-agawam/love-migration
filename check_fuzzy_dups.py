#!/usr/bin/env python3
import subprocess
import json
from difflib import SequenceMatcher

# Query all account names
result = subprocess.run(
    ['sfdx', 'data', 'query',
     '--query', 'SELECT Id, Name FROM Account ORDER BY Name LIMIT 5000',
     '-o', 'mike@lovementoring.org.maylove',
     '--json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
if data.get('status') != 0:
    print(f"Query failed: {data.get('message')}")
    exit(1)

accounts = data['result']['records']
names = [r['Name'] for r in accounts]

print(f"Analyzing {len(names)} account names for fuzzy duplicates...\n")

# Find similar names (threshold 0.85 = 85% match)
potential_dups = []
threshold = 0.85

for i in range(len(names)):
    for j in range(i + 1, len(names)):
        ratio = SequenceMatcher(None, names[i].lower(), names[j].lower()).ratio()
        if ratio >= threshold:
            potential_dups.append({
                'name1': names[i],
                'name2': names[j],
                'similarity': ratio
            })

if potential_dups:
    print(f"⚠️  FOUND {len(potential_dups)} POTENTIAL FUZZY DUPLICATES:\n")
    # Sort by similarity score descending
    for dup in sorted(potential_dups, key=lambda x: x['similarity'], reverse=True):
        print(f"  {dup['similarity']:.1%} match:")
        print(f"    - {dup['name1']}")
        print(f"    - {dup['name2']}\n")
else:
    print(f"✓ No fuzzy duplicate names found (threshold: {threshold:.0%})")
    print(f"  Total accounts analyzed: {len(names)}")
