"""
Use Salesforce REST API to update Contact records with enrichment data.
Bypasses SOQL caching issues by using direct API calls.
"""
import json
import csv
import subprocess
import sys

def get_access_token(org_alias):
    """Get access token for org."""
    result = subprocess.run(
        ["sf", "org", "display", "-o", org_alias, "--json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return data["result"]["accessToken"], data["result"]["instanceUrl"]

def load_enrichment_data():
    """Load enrichment data from CSV."""
    enrichment = {}
    try:
        with open("source_indiv_by_date.csv", "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                first = row.get("First Name", "").strip()
                last = row.get("Last Name", "").strip()
                mailchimp = row.get("MailChimp?", "").strip()
                note = row.get("Note", "").strip()
                
                # Key by "FirstName LastName" for lookup
                key = f"{first} {last}"
                enrichment[key] = {
                    "MailChimp_Status__c": mailchimp if mailchimp else None,
                    "Donor_MailChimp__c": mailchimp if mailchimp else None,
                    "Note__c": note if note else None,
                    "Donor_Note__c": note if note else None,
                }
    except FileNotFoundError:
        print("ERROR: source_indiv_by_date.csv not found")
        sys.exit(1)
    
    return enrichment

def update_contacts_via_rest(token, instance_url, enrichment_data):
    """Update Contact records using REST API."""
    import urllib.request
    import urllib.error
    
    # First, get all contacts with names
    query_url = f"{instance_url}/services/data/v59.0/query?q=SELECT+Id,FirstName,LastName+FROM+Contact"
    
    req = urllib.request.Request(query_url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    
    try:
        with urllib.request.urlopen(req) as response:
            contacts_data = json.loads(response.read())
    except urllib.error.URLError as e:
        print(f"ERROR querying contacts: {e}")
        sys.exit(1)
    
    contacts = contacts_data.get("records", [])
    print(f"Found {len(contacts)} contacts")
    
    updated_count = 0
    for contact in contacts:
        contact_id = contact["Id"]
        first = contact.get("FirstName", "").strip()
        last = contact.get("LastName", "").strip()
        key = f"{first} {last}"
        
        if key in enrichment_data:
            update_data = enrichment_data[key]
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            
            if not update_data:
                continue
            
            # Update via PATCH
            update_url = f"{instance_url}/services/data/v59.0/sobjects/Contact/{contact_id}"
            req = urllib.request.Request(update_url, data=json.dumps(update_data).encode())
            req.add_header("Authorization", f"Bearer {token}")
            req.add_header("Content-Type", "application/json")
            req.get_method = lambda: "PATCH"
            
            try:
                with urllib.request.urlopen(req) as response:
                    updated_count += 1
                    if updated_count % 50 == 0:
                        print(f"  Updated {updated_count} contacts...")
            except urllib.error.URLError as e:
                print(f"ERROR updating {contact_id}: {e}")
    
    print(f"\n✓ Updated {updated_count} contacts with enrichment data")

def main():
    org = "mike@lovementoring.org.maylove"
    
    print("1. Loading enrichment data...")
    enrichment = load_enrichment_data()
    print(f"   Loaded {len(enrichment)} enrichment records")
    
    print("\n2. Getting access token...")
    token, instance_url = get_access_token(org)
    print(f"   Instance: {instance_url}")
    
    print("\n3. Updating contacts via REST API...")
    update_contacts_via_rest(token, instance_url, enrichment)
    
    print("\n✓ Done!")

if __name__ == "__main__":
    main()
