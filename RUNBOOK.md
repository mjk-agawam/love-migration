# L.O.V.E. Salesforce Migration — Update Runbook

## What this does
Syncs data from Google Sheets → Salesforce sandbox (`mike@lovementoring.org.maylove`).  
All 6 object types are upserted idempotently — safe to re-run as many times as needed.

## When the customer requests changes

### Step 1 — Update the source CSVs
Open Claude Code in this directory and say:  
**"The customer changed [X]. Please update the source CSVs and re-run."**

Claude will read the affected Google Sheet tabs via MCP and rewrite the relevant `source_*.csv` files:

| File | Source tab | Used for |
|---|---|---|
| `source_ready_for_contacts.csv` | Ready For Contacts | Org Accounts + Contacts + Opps (steps 1-3) |
| `source_ready_for_accounts.csv` | Ready For Accounts | Org Accounts fallback |
| `source_indiv_board.csv` | Individual-Board | Board donors |
| `source_indiv_amigos.csv` | Indiv-Amigos | Amigos donors |
| `source_indiv_campaneros.csv` | Indiv-Campaneros | Campaneros donors |
| `source_indiv_aliados.csv` | Indiv-Aliados | Aliados donors |

### Step 2 — Run the sync
```bash
python3 sync.py              # full sync (all 6 steps)
python3 sync.py --dry-run    # preview without touching SF
python3 sync.py --step 4     # run only one step (1=org accts, 2=org contacts, 3=org opps, 4=indiv accts, 5=indiv contacts, 6=indiv opps)
```

## SF Sandbox
- Org alias: `mike@lovementoring.org.maylove`
- NPSP Household record type: `012f2000000ww91AAA`
- Organization record type: `012f2000000ww92AAA`
- External ID fields: `Account_External_ID__c`, `Contact_External_ID__c`, `Opportunity_External_ID__c`

## Source spreadsheet
TRANSFORM sheet ID: `1DcN69Yw-H_LRL9W7UP93EtTmv81_kRrNNgjgYX4dkp0`  
(Claude reads it via Google Workspace MCP — no auth setup needed)

## Expected record counts (as of 2026-06-03)
- Org Accounts: ~47
- Org Contacts: ~57
- Org Opportunities: ~47
- Individual Accounts: 227
- Individual Contacts: 227
- Individual Opportunities: ~139
