"""
Update Contact records with enrichment data, matching by email.
"""
import json
import csv
import subprocess

def load_enrichment_data():
    """Load enrichment data from CSV, keyed by email."""
    enrichment = {}
    with open("source_indiv_by_date.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("Email Address", "").strip().lower()
            mailchimp = row.get("MailChimp?", "").strip()
            note = row.get("Note", "").strip()
            
            if email and email != "not shared by donor":
                enrichment[email] = {
                    "mailchimp": mailchimp,
                    "note": note,
                }
    return enrichment

def get_contacts(org):
    """Get all contacts with email using sf CLI."""
    result = subprocess.run(
        ["sf", "data", "query", 
         "--query", "SELECT Id, FirstName, LastName FROM Contact LIMIT 500",
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
    
    # Now get contacts with email
    print("3. Querying contacts WITH email...")
    result = subprocess.run(
        ["sf", "data", "query", 
         "--query", "SELECT Id, FirstName, LastName FROM Contact WHERE Email != null LIMIT 500",
         "-o", org, "--json"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        contacts_with_email = data.get("result", {}).get("records", [])
        print(f"   Found {len(contacts_with_email)} contacts with email\n")
    else:
        print(f"   ERROR: {result.stderr}\n")
        contacts_with_email = []
    
    # Sample a few to see what we're working with
    if contacts_with_email:
        print("   Sample contacts:")
        for c in contacts_with_email[:3]:
            print(f"     {c['FirstName']} {c['LastName']} ({c['Id']})")

if __name__ == "__main__":
    main()
