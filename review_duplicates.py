#!/usr/bin/env python3
import subprocess
import json

# List of 100% duplicate names
duplicates = [
    "Christian and Christian Audi Household",
    "Eric and Eric Gregware Household",
    "M&T Charitable Fund",
    "Odalys and Odalys Ramos Household",
    "Shireesha and Shireesha Nethi Household",
    "The Slomo & Cindy Siivian Foundation",
    "Tiago and Tiago Rachelson Household",
    "Walter and Walter Luna de Leon Household"
]

def review_duplicate(name):
    """Query and display duplicate records for a given name"""
    result = subprocess.run(
        ['sfdx', 'data', 'query',
         '--query', f"SELECT Id, Name, Account_External_ID__c, RecordType.Name, Type, Relationship__c, BillingStreet, BillingCity, BillingState, BillingPostalCode, Phone, Website, Description FROM Account WHERE Name = '{name}'",
         '-o', 'mike@lovementoring.org.maylove',
         '--json'],
        capture_output=True,
        text=True
    )

    data = json.loads(result.stdout)
    if data.get('status') != 0:
        print(f"Query failed: {data.get('message')}\n")
        return False

    records = data['result']['records']
    print(f"{'='*100}")
    print(f"DUPLICATE: {name}")
    print(f"Found {len(records)} records\n")

    for idx, r in enumerate(records, 1):
        print(f"Record {idx}:")
        print(f"  ID:                {r.get('Id')}")
        print(f"  Name:              {r.get('Name')}")
        print(f"  External ID:       {r.get('Account_External_ID__c')}")
        print(f"  Record Type:       {r.get('RecordType', {}).get('Name', 'N/A')}")
        print(f"  Type:              {r.get('Type')}")
        print(f"  Relationship:      {r.get('Relationship__c')}")
        print(f"  Billing Street:    {r.get('BillingStreet')}")
        print(f"  Billing City:      {r.get('BillingCity')}")
        print(f"  Billing State:     {r.get('BillingState')}")
        print(f"  Billing Postal:    {r.get('BillingPostalCode')}")
        print(f"  Phone:             {r.get('Phone')}")
        print(f"  Website:           {r.get('Website')}")
        print(f"  Description:       {r.get('Description')[:100] if r.get('Description') else 'N/A'}")
        print()

    return True

# Review first duplicate
if len(duplicates) > 0:
    review_duplicate(duplicates[0])
    print("\nNext duplicate to review: Christian and Christian Audi Household")
    print("Type: next() to continue to the next duplicate")
