"""
Create a donor details report showing Contact + Opportunity + Account data.
Uses the REST API to create the report directly.
"""
import json
import subprocess

def create_report(org):
    """Create a tabular report of donor data."""
    
    # Report definition using REST API
    report_config = {
        "reportName": "Donor Details - Enriched",
        "reportDescription": "Donor contact information with donations and enrichment data",
        "reportType": "OpportunityContact",
        "reportFormat": "TABULAR",
        "reportBooleanFilter": "",
        "showTotals": True,
        "showGrandTotals": True,
        "groupingColumn": ["CONTACT_FIRSTNAME"],
        "columns": [
            "CONTACT_FIRSTNAME",
            "CONTACT_LASTNAME",
            "CONTACT_EMAIL",
            "CONTACT_PHONE",
            "OPPORTUNITY_AMOUNT",
            "OPPORTUNITY_CLOSE_DATE",
            "ACCOUNT_NAME",
        ],
    }
    
    # For now, just print the config
    print("Report configuration that would be created:")
    print(json.dumps(report_config, indent=2))

if __name__ == "__main__":
    org = "mike@lovementoring.org.maylove"
    create_report(org)
