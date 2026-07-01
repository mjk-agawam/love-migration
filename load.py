"""
L.O.V.E. Salesforce load script.

Reads TRANSFORM Google Sheet and upserts:
  1. Accounts  (orgs from Ready For Accounts + households for individuals)
  2. Contacts  (from Ready For Contacts + individual tabs)
  3. Opportunities (from Ready For Contacts grant amounts + individual donation years)

Run:
    uv run python load.py [--dry-run]

First run opens a browser for Google OAuth. Credentials cached at ~/.config/gspread/credentials.json.
Salesforce credentials pulled from active `sf` CLI session.
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import date
from typing import Optional

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from simple_salesforce import Salesforce

# ── Constants ────────────────────────────────────────────────────────────────

TRANSFORM_SHEET_ID = "1DcN69Yw-H_LRL9W7UP93EtTmv81_kRrNNgjgYX4dkp0"
SF_ORG_ALIAS = "mike@lovementoring.org.maylove"

PLACEHOLDER_EMAIL = "no_email_given@not.given"

# Application Status → Opportunity Stage mapping
STAGE_MAP = {
    "in progress":        "Application Submitted",
    "submitted":          "Application Submitted",
    "loi submitted":      "LOI Submitted",
    "granted":            "Closed Won",
    "closed won":         "Closed Won",
    "declined":           "Declined",
    "closed lost":        "Closed Lost",
    "not submitted":      "Prospecting",
    "prospect":           "Prospecting",
    "prospecting":        "Prospecting",
    "cultivating":        "Cultivating",
    "cultivation":        "Cultivation",
    "ng":                 "Closed Lost",
    "":                   "Prospecting",
}

KNOWN_DUPLICATES = [
    "LUCHA (Latin United Community Housing Association) appears in rows 24 and 28 — load both, clean up in Salesforce.",
    "Lily Auchincloss Foundation appears in rows 10 and 33 with slightly different names — load both, clean up in Salesforce.",
    "COMPASS (26026P0003) appears in rows 29, 30, 31 — kept separate (different competition pools per column B).",
]

# Record type IDs (from org describe)
RT_HOUSEHOLD = "012f2000000ww91AAA"
RT_ORGANIZATION = "012f2000000ww92AAA"

# ── Helpers ──────────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text).strip())
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", text.lower())


def clean_amount(value: str) -> Optional[float]:
    """Parse a donation amount string to float. Returns None for blank/dash/zero."""
    v = str(value).strip()
    if not v or v in ("-", "—", "$0", "0"):
        return None
    # Strip currency symbols, commas, spaces, parentheses
    v = re.sub(r"[$,\s]", "", v)
    # Handle ranges like "$5,000 - $25,000" — take first number
    v = re.split(r"[-–—]", v)[0].strip()
    try:
        amount = float(v)
        return amount if amount > 0 else None
    except ValueError:
        return None


def clean_email(raw: str) -> str:
    """Return first valid-looking email from a cell, or placeholder."""
    raw = str(raw).strip()
    if not raw or raw in ("—", "-", "N/A"):
        return ""
    # Cell may contain multiple emails separated by spaces, semicolons, commas, or newlines
    candidates = re.split(r"[\s;,\n]+", raw)
    for c in candidates:
        c = c.strip()
        if "@" in c and "." in c.split("@")[-1]:
            return c.lower()
    return ""


def is_blank(value: str) -> bool:
    return str(value).strip() in ("", "—", "-", "N/A", "None")


def map_stage(status: str) -> str:
    key = str(status).strip().lower()
    # Handle prefixes like "NG 9/29"
    for k, v in STAGE_MAP.items():
        if k and key.startswith(k):
            return v
    return STAGE_MAP.get(key, "Prospecting")


def year_from_header(header: str) -> Optional[int]:
    """Extract 4-digit year from headers like '2026', '$2,026', 'Amount donated 2024'."""
    header = re.sub(r"[$,]", "", str(header))
    match = re.search(r"(20\d{2})", header)
    return int(match.group(1)) if match else None


def get_sf_session() -> Salesforce:
    """Pull active sf CLI session for the sandbox org."""
    result = subprocess.run(
        ["sf", "org", "display", "--target-org", SF_ORG_ALIAS, "--json"],
        capture_output=True, text=True, check=True,
    )
    info = json.loads(result.stdout)["result"]
    return Salesforce(
        instance_url=info["instanceUrl"],
        session_id=info["accessToken"],
    )


def get_gspread_client() -> gspread.Client:
    """Authenticate with Google Sheets via OAuth, caching credentials."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds_dir = os.path.expanduser("~/.config/gspread")
    token_path = os.path.join(creds_dir, "token.pickle")
    client_secret_path = os.path.join(creds_dir, "credentials.json")

    creds = None
    if os.path.exists(token_path):
        with open(token_path) as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, scopes)
            creds = flow.run_local_server(port=0)
        os.makedirs(creds_dir, exist_ok=True)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return gspread.authorize(creds)


# ── Sheet readers ─────────────────────────────────────────────────────────────

def read_sheet(gc: gspread.Client, sheet_id: str, tab_name: str) -> list[dict]:
    """Read a tab and return list of row dicts keyed by header row 1."""
    ws = gc.open_by_key(sheet_id).worksheet(tab_name)
    rows = ws.get_all_values()
    if not rows:
        return []
    headers = rows[0]
    result = []
    for row in rows[1:]:
        # Pad short rows
        padded = row + [""] * (len(headers) - len(row))
        result.append(dict(zip(headers, padded)))
    return result


def get_email_for_row(row: dict, email_col: str = "Email Address",
                       cleanup_col: str = "Email Cleanup") -> str:
    """Return cleaned email: prefer cleanup column, fall back to source column."""
    cleanup = clean_email(row.get(cleanup_col, ""))
    if cleanup and cleanup != PLACEHOLDER_EMAIL:
        return cleanup
    # Check if cleanup col has placeholder
    raw_cleanup = str(row.get(cleanup_col, "")).strip()
    if raw_cleanup == PLACEHOLDER_EMAIL:
        return PLACEHOLDER_EMAIL
    return clean_email(row.get(email_col, ""))


# ── Load: Org Accounts (Ready For Accounts) ──────────────────────────────────

def load_org_accounts(sf: Salesforce, rows: list[dict], dry_run: bool) -> dict[str, str]:
    """Upsert org Accounts. Returns {external_id: sf_id}."""
    print("\n=== Loading Org Accounts ===")
    id_map = {}
    errors = []

    for row in rows:
        name = str(row.get("Name", "")).strip()
        ext_id = str(row.get("External ID", "")).strip()
        if not name or not ext_id:
            continue

        record = {
            "Name": name,
            "RecordTypeId": RT_ORGANIZATION,
            "Account_External_ID__c": ext_id,
            "Geographic_Scope__c": row.get("Location", "")[:255] or None,
            "Area_of_Interest__c": row.get("Area of interest ", "")[:32000] or None,
            "Account_Information__c": row.get("Account Information ", "")[:32000] or None,
            "Documentation_Requirements__c": row.get("Documentation and Requirements ", "")[:32000] or None,
            "Internal_Notes__c": row.get("Notes", "")[:32000] or None,
            "Research_Links__c": row.get("Research_Links__c", "")[:255] or None,
        }
        # Remove None values
        record = {k: v for k, v in record.items() if v is not None and v != ""}

        if dry_run:
            print(f"  [DRY RUN] Upsert Account: {name} ({ext_id})")
            id_map[ext_id] = f"DRY_{ext_id}"
        else:
            try:
                result = sf.Account.upsert(f"Account_External_ID__c/{ext_id}", record)
                sf_id = result.get("id") or ext_id
                id_map[ext_id] = sf_id
                print(f"  ✓ Account: {name}")
            except Exception as e:
                errors.append(f"Account {name}: {e}")
                print(f"  ✗ Account {name}: {e}")

    if errors:
        print(f"\n  {len(errors)} account error(s).")
    return id_map


# ── Load: Org Contacts (Ready For Contacts) ───────────────────────────────────

def load_org_contacts(sf: Salesforce, rows: list[dict],
                      account_id_map: dict[str, str], dry_run: bool):
    """Upsert Contacts linked to org Accounts."""
    print("\n=== Loading Org Contacts ===")
    errors = []

    for row in rows:
        acct_name = str(row.get("Name", "")).strip()
        acct_ext_id = str(row.get("Account1 External ID", "")).strip()
        if not acct_name or not acct_ext_id:
            continue

        acct_sf_id = account_id_map.get(acct_ext_id)

        # Up to 3 contacts per row
        for i in range(1, 4):
            if i == 1:
                first = str(row.get("Contact 1First", "")).strip()
                last = str(row.get("Contact 1Last", "")).strip()
                title_raw = str(row.get("Title1 NameRaw", "")).strip()
                email_raw = str(row.get("Email1 NameRaw", "")).strip()
            elif i == 2:
                first = str(row.get("Contact 2 First", "")).strip()
                last = str(row.get("Contact 2 Last", "")).strip()
                title_raw = str(row.get("Title2 NameRaw", "")).strip()
                email_raw = str(row.get("Email2 NameRaw", "")).strip()
            else:
                first = str(row.get("Contact 3 First", "")).strip()
                last = str(row.get("Contact 3 Last", "")).strip()
                title_raw = str(row.get("Title3 NameRaw", row.get("Title3 NameRaw.1", "")), "").strip()
                email_raw = str(row.get("Title3 NameRaw.1", "")).strip()

            if is_blank(first) and is_blank(last):
                continue

            email = clean_email(email_raw)
            title = "" if is_blank(title_raw) else title_raw

            # External ID: acct_ext_id + contact number
            contact_ext_id = f"{acct_ext_id}_c{i}"

            record = {
                "FirstName": first or None,
                "LastName": last if last else "(unknown)",
                "Title": title or None,
                "Email": email or None,
                "Contact_External_ID__c": contact_ext_id,
            }
            if acct_sf_id:
                record["AccountId"] = acct_sf_id
            record = {k: v for k, v in record.items() if v is not None}

            if dry_run:
                print(f"  [DRY RUN] Upsert Contact: {first} {last} @ {acct_name}")
            else:
                try:
                    sf.Contact.upsert(f"Contact_External_ID__c/{contact_ext_id}", record)
                    print(f"  ✓ Contact: {first} {last} @ {acct_name}")
                except Exception as e:
                    errors.append(f"Contact {first} {last}: {e}")
                    print(f"  ✗ Contact {first} {last}: {e}")

    if errors:
        print(f"\n  {len(errors)} contact error(s).")


# ── Load: Org Opportunities (Ready For Contacts) ──────────────────────────────

def load_org_opportunities(sf: Salesforce, rows: list[dict],
                           account_id_map: dict[str, str], dry_run: bool):
    """Upsert one Opportunity per org account row."""
    print("\n=== Loading Org Opportunities ===")
    errors = []

    for row in rows:
        acct_name = str(row.get("Name", "")).strip()
        acct_ext_id = str(row.get("Account1 External ID", "")).strip()
        if not acct_name or not acct_ext_id:
            continue

        acct_sf_id = account_id_map.get(acct_ext_id)
        status = str(row.get("Outreach_Status__c", row.get("Application Status", ""))).strip()
        stage = map_stage(status)
        amount = clean_amount(row.get("Grant Amount", row.get("Grant_Amount_Text__c", "")))
        due_date_raw = str(row.get("Due Date", row.get("Due_Date_Text__c", ""))).strip()

        opty_ext_id = f"{acct_ext_id}_opty"
        opty_name = f"{acct_name} Grant"

        record = {
            "Name": opty_name,
            "StageName": stage,
            "CloseDate": str(date.today()),
            "Opportunity_External_ID__c": opty_ext_id,
        }
        if amount:
            record["Amount"] = amount
        if acct_sf_id:
            record["AccountId"] = acct_sf_id

        record = {k: v for k, v in record.items() if v is not None}

        if dry_run:
            print(f"  [DRY RUN] Upsert Opportunity: {opty_name} | Stage: {stage} | Amount: {amount}")
        else:
            try:
                sf.Opportunity.upsert(f"Opportunity_External_ID__c/{opty_ext_id}", record)
                print(f"  ✓ Opportunity: {opty_name} | Stage: {stage}")
            except Exception as e:
                errors.append(f"Opportunity {opty_name}: {e}")
                print(f"  ✗ Opportunity {opty_name}: {e}")

    if errors:
        print(f"\n  {len(errors)} opportunity error(s).")


# ── Load: Individual Households + Contacts + Opportunities ───────────────────

def load_individuals(sf: Salesforce, gc: gspread.Client, dry_run: bool):
    """Load individuals from all four donor tabs as NPSP Household Accounts."""
    print("\n=== Loading Individual Donors ===")

    tabs = [
        ("Individual-Board",   "AccountExternalID", "ContactExternalID", "OptyExternalID",
         ["Amount donated 2026", "Amount donated 2025", "Amount donated 2024",
          "Amount donated 2023", "Amount donated 2022", "Amount donated 2021"],
         "Email Address", "Email Cleanup"),
        ("Indiv-Amigos",       "AccountExternalID", "ContactExternalID", "OptyExternalID",
         ["2026", "2025", "2024", "2023", "2022"],
         "Email Address", "Email Cleanup"),
        ("Indiv-Campaneros",   "AccountExternalID", "ContactExternalID", "OptyExternalID",
         ["$2,026", "$2,025", "$2,024", "$2,023", "$2,022", "2021"],
         "Email Address", "Email Clean Up"),
        ("Indiv-Aliados",      "AccountExternalID", "ContactExternalID", "OptyExternalID",
         ["2026", "2025", "2024", "2023", "2022"],
         "Email Address", "Email Clean Up"),
    ]

    errors = []

    for tab_name, acct_ext_col, cont_ext_col, opty_ext_col, year_cols, email_col, cleanup_col in tabs:
        print(f"\n  Tab: {tab_name}")
        rows = read_sheet(gc, TRANSFORM_SHEET_ID, tab_name)

        for row in rows:
            first = str(row.get("First Name", "")).strip()
            last = str(row.get("Last Name", "")).strip()
            if not first and not last:
                continue

            acct_ext_id = str(row.get(acct_ext_col, "")).strip()
            cont_ext_id = str(row.get(cont_ext_col, "")).strip()
            if not acct_ext_id:
                continue

            email = get_email_for_row(row, email_col, cleanup_col)
            full_name = f"{first} {last}".strip()
            household_name = f"{last} Household"

            # Upsert Household Account
            acct_record = {
                "Name": household_name,
                "RecordTypeId": RT_HOUSEHOLD,
                "Account_External_ID__c": acct_ext_id,
            }
            if dry_run:
                print(f"    [DRY RUN] Household: {household_name}")
                acct_sf_id = f"DRY_{acct_ext_id}"
            else:
                try:
                    result = sf.Account.upsert(f"Account_External_ID__c/{acct_ext_id}", acct_record)
                    acct_sf_id = result.get("id") or acct_ext_id
                    print(f"    ✓ Household: {household_name}")
                except Exception as e:
                    errors.append(f"Household {household_name}: {e}")
                    print(f"    ✗ Household {household_name}: {e}")
                    continue

            # Upsert Contact
            cont_record = {
                "FirstName": first or None,
                "LastName": last if last else "(unknown)",
                "Email": email or None,
                "AccountId": acct_sf_id,
                "Contact_External_ID__c": cont_ext_id,
            }
            cont_record = {k: v for k, v in cont_record.items() if v is not None}

            if dry_run:
                print(f"    [DRY RUN] Contact: {full_name} | email: {email or '(blank)'}")
            else:
                try:
                    sf.Contact.upsert(f"Contact_External_ID__c/{cont_ext_id}", cont_record)
                    print(f"    ✓ Contact: {full_name}")
                except Exception as e:
                    errors.append(f"Contact {full_name}: {e}")
                    print(f"    ✗ Contact {full_name}: {e}")

            # Upsert one Opportunity per non-zero donation year
            for year_header in year_cols:
                amount = clean_amount(row.get(year_header, ""))
                if not amount:
                    continue
                year = year_from_header(year_header)
                if not year:
                    continue

                opty_ext_id = f"{acct_ext_id}_donation_{year}"
                opty_record = {
                    "Name": f"{full_name} Donation {year}",
                    "StageName": "Closed Won",
                    "Amount": amount,
                    "CloseDate": f"{year}-12-31",
                    "AccountId": acct_sf_id,
                    "Opportunity_External_ID__c": opty_ext_id,
                }
                if dry_run:
                    print(f"    [DRY RUN] Opportunity: {year} ${amount}")
                else:
                    try:
                        sf.Opportunity.upsert(
                            f"Opportunity_External_ID__c/{opty_ext_id}", opty_record
                        )
                        print(f"    ✓ Opportunity: {full_name} {year} ${amount}")
                    except Exception as e:
                        errors.append(f"Opportunity {full_name} {year}: {e}")
                        print(f"    ✗ Opportunity {full_name} {year}: {e}")

    if errors:
        print(f"\n  {len(errors)} individual error(s).")
    return errors


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be loaded without writing to Salesforce")
    args = parser.parse_args()

    if args.dry_run:
        print("*** DRY RUN — no data will be written to Salesforce ***\n")

    # Print known duplicates notice
    print("=== Known Duplicates (will load all, flag for customer cleanup) ===")
    for note in KNOWN_DUPLICATES:
        print(f"  • {note}")

    print("\nConnecting to Salesforce...")
    sf = get_sf_session()
    print(f"  Connected: {sf.sf_instance}")

    print("Connecting to Google Sheets...")
    gc = get_gspread_client()
    print("  Connected.")

    # Read sheets
    print("\nReading TRANSFORM sheet...")
    acct_rows = read_sheet(gc, TRANSFORM_SHEET_ID, "Ready For Accounts")
    contact_rows = read_sheet(gc, TRANSFORM_SHEET_ID, "Ready For Contacts")
    print(f"  Ready For Accounts: {len(acct_rows)} rows")
    print(f"  Ready For Contacts: {len(contact_rows)} rows")

    # Load in order: Accounts → Contacts → Opportunities
    account_id_map = load_org_accounts(sf, acct_rows, args.dry_run)
    load_org_contacts(sf, contact_rows, account_id_map, args.dry_run)
    load_org_opportunities(sf, contact_rows, account_id_map, args.dry_run)
    load_individuals(sf, gc, args.dry_run)

    print("\n=== Load complete ===")


if __name__ == "__main__":
    main()
