"""
Use sf CLI to update Contact records with enrichment data via REST API.
"""
import json
import csv
import subprocess

def load_enrichment_data():
    """Load enrichment data from CSV, keyed by FirstName+LastName."""
    enrichment = {}
    with open("source_indiv_by_date.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            first = row.get("First Name", "").strip()
            last = row.get("Last Name", "").strip()
            mailchimp = row.get("MailChimp?", "").strip()
            note = row.get("Note", "").strip()
            
            key = f"{first} {last}".lower()
            enrichment[key] = {
                "mailchimp": mailchimp,
                "note": note,
            }
    return enrichment

def get_contacts(org):
    """Get all contacts using sf CLI."""
    result = subprocess.run(
        ["sf", "data", "query", "--query", "SELECT Id, FirstName, LastName FROM Contact",
         "-o", org, "--json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return []
    
    data = json.loads(result.stdout)
    return data.get("result", {}).get("records", [])

def update_contact(org, contact_id, update_data):
    """Update a single contact using sf CLI."""
    json_str = json.dumps(update_data).replace('"', '\\"')
    result = subprocess.run(
        ["sf", "data", "update", "record", "--sobject", "Contact", "--record-id", contact_id,
         "--values", json_str, "-o", org],
        capture_output=True, text=True
    )
    return result.returncode == 0

def main():
    org = "mike@lovementoring.org.maylove"
    
    print("1. Loading enrichment data...")
    enrichment = load_enrichment_data()
    print(f"   Loaded {len(enrichment)} enrichment records\n")
    
    print("2. Querying contacts...")
    contacts = get_contacts(org)
    print(f"   Found {len(contacts)} contacts\n")
    
    print("3. Updating contacts...")
    updated = 0
    for contact in contacts:
        contact_id = contact["Id"]
        first = contact.get("FirstName", "").strip()
        last = contact.get("LastName", "").strip()
        key = f"{first} {last}".lower()
        
        if key in enrichment:
            data = enrichment[key]
            update_data = {}
            
            if data["mailchimp"]:
                update_data["MailChimp_Status__c"] = data["mailchimp"]
                update_data["Donor_MailChimp__c"] = data["mailchimp"]
            
            if data["note"]:
                update_data["Note__c"] = data["note"]
                update_data["Donor_Note__c"] = data["note"]
            
            if update_data:
                if update_contact(org, contact_id, update_data):
                    updated += 1
                    if updated % 10 == 0:
                        print(f"   Updated {updated}...")
    
    print(f"\n✓ Updated {updated} contacts with enrichment data")

if __name__ == "__main__":
    main()
