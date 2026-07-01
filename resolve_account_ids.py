"""Query SF for Account IDs by external ID, then produce load-ready contacts and opps CSVs.

Usage: python3 resolve_account_ids.py
Outputs:
  indiv_contacts_load.csv
  indiv_opps_load.csv
"""
import csv
import json
import re
import subprocess
import sys

PROJ = '/Users/mikeknight/Projects/love-migration'
SF_ORG = 'mike@lovementoring.org.maylove'


def sf_query(soql):
    result = subprocess.run(
        ['sf', 'data', 'query', '--target-org', SF_ORG,
         '--query', soql, '--result-format', 'json'],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)['result']['records']


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_csv(path, fieldnames, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


# Load ext IDs from accounts CSV
acct_rows = read_csv(f'{PROJ}/indiv_accounts.csv')
ext_ids = [r['Account_External_ID__c'] for r in acct_rows]

print(f"Querying SF for {len(ext_ids)} account external IDs...", file=sys.stderr)

# Query in batches of 200 (SOQL IN clause limit)
ext_to_sfid = {}
batch_size = 200
for i in range(0, len(ext_ids), batch_size):
    batch = ext_ids[i:i+batch_size]
    ids_str = "','".join(batch)
    soql = f"SELECT Id, Account_External_ID__c FROM Account WHERE Account_External_ID__c IN ('{ids_str}')"
    records = sf_query(soql)
    for rec in records:
        ext_to_sfid[rec['Account_External_ID__c']] = rec['Id']
    print(f"  Batch {i//batch_size + 1}: got {len(records)} records", file=sys.stderr)

print(f"Resolved {len(ext_to_sfid)} of {len(ext_ids)} accounts", file=sys.stderr)

missing = [e for e in ext_ids if e not in ext_to_sfid]
if missing:
    print(f"WARNING: {len(missing)} ext IDs not found in SF:", file=sys.stderr)
    for m in missing[:20]:
        print(f"  {m}", file=sys.stderr)

# Build contacts load CSV
cont_rows = read_csv(f'{PROJ}/indiv_contacts.csv')
cont_out = []
cont_skipped = 0
for r in cont_rows:
    ext_id = r['AccountId']
    sf_id = ext_to_sfid.get(ext_id)
    if not sf_id:
        cont_skipped += 1
        continue
    cont_out.append({
        'Contact_External_ID__c': r['Contact_External_ID__c'],
        'FirstName': r['FirstName'],
        'LastName': r['LastName'],
        'Email': r['Email'],
        'AccountId': sf_id,
    })

write_csv(f'{PROJ}/indiv_contacts_load.csv',
          ['Contact_External_ID__c', 'FirstName', 'LastName', 'Email', 'AccountId'], cont_out)
print(f"Contacts: {len(cont_out)} written, {cont_skipped} skipped → indiv_contacts_load.csv", file=sys.stderr)

# Build opps load CSV
opp_rows = read_csv(f'{PROJ}/indiv_opps.csv')
opp_out = []
opp_skipped = 0
for r in opp_rows:
    ext_id = r['AccountId']
    sf_id = ext_to_sfid.get(ext_id)
    if not sf_id:
        opp_skipped += 1
        continue
    opp_out.append({
        'Opportunity_External_ID__c': r['Opportunity_External_ID__c'],
        'Name': r['Name'],
        'StageName': r['StageName'],
        'CloseDate': r['CloseDate'],
        'Amount': r['Amount'],
        'AccountId': sf_id,
    })

write_csv(f'{PROJ}/indiv_opps_load.csv',
          ['Opportunity_External_ID__c', 'Name', 'StageName', 'CloseDate', 'Amount', 'AccountId'], opp_out)
print(f"Opps: {len(opp_out)} written, {opp_skipped} skipped → indiv_opps_load.csv", file=sys.stderr)
