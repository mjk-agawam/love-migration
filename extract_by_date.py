"""
Extract By Date tab from Google Sheet and generate source_indiv_by_date.csv.

Row 14 contains headers. Rows 15+ contain donor data.
Extract: First Name, Last Name, MailChimp?, Home Address, Note columns.

Usage:
    python3 extract_by_date.py

On first run, opens browser for Google OAuth.
"""

import gspread
import csv
import sys

SHEET_ID = "1kg7tGBfOi5zg3qzauCCBvciyI7BD888UERbA5c2Mfis"
OUTPUT_FILE = "source_indiv_by_date.csv"


def extract_by_date_tab():
    """Connect to Google Sheet and extract By Date tab data."""
    gc = gspread.oauth()
    sheet = gc.open_by_key(SHEET_ID)

    # Find "By Date" worksheet
    ws = None
    for w in sheet.worksheets():
        if "By Date" in w.title:
            ws = w
            break

    if not ws:
        print("ERROR: 'By Date' worksheet not found")
        print("Available worksheets:")
        for w in sheet.worksheets():
            print(f"  - {w.title}")
        sys.exit(1)

    print(f"Found worksheet: {ws.title}")

    # Get row 14 (header row)
    headers = ws.row_values(14)
    print(f"\nRow 14 has {len(headers)} columns")

    # Find column indices for the fields we need
    col_map = {}
    for idx, header in enumerate(headers, 1):
        if header and (header == "First Name" or
                      header == "Last Name" or
                      header == "MailChimp?" or
                      header == "Home Address" or
                      header == "Note"):
            col_map[header] = idx - 1  # 0-based for list indexing
            print(f"  Column {idx}: {header}")

    if not all(key in col_map for key in ["First Name", "Last Name", "MailChimp?", "Home Address", "Note"]):
        print("\nERROR: Not all required columns found in row 14")
        print(f"Found: {list(col_map.keys())}")
        sys.exit(1)

    # Extract all rows starting from row 15
    all_values = ws.get_values()

    # Row 15 is index 14 (0-based)
    data_rows = all_values[14:]  # Skip headers (row 14 = index 13, so 14 onwards is data)

    print(f"\nExtracting {len(data_rows)} data rows...")

    # Write to CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["First Name", "Last Name", "MailChimp?", "Home Address", "Note"])
        writer.writeheader()

        for row_idx, row in enumerate(data_rows, 15):
            # Ensure row has enough columns
            while len(row) <= max(col_map.values()):
                row.append('')

            first_name = row[col_map["First Name"]].strip() if col_map["First Name"] < len(row) else ''
            last_name = row[col_map["Last Name"]].strip() if col_map["Last Name"] < len(row) else ''

            # Skip empty rows
            if not first_name and not last_name:
                continue

            mailchimp = row[col_map["MailChimp?"]].strip() if col_map["MailChimp?"] < len(row) else ''
            home_addr = row[col_map["Home Address"]].strip() if col_map["Home Address"] < len(row) else ''
            note = row[col_map["Note"]].strip() if col_map["Note"] < len(row) else ''

            writer.writerow({
                "First Name": first_name,
                "Last Name": last_name,
                "MailChimp?": mailchimp,
                "Home Address": home_addr,
                "Note": note,
            })

    # Count rows written
    with open(OUTPUT_FILE, 'r') as f:
        count = sum(1 for line in f) - 1  # Subtract header

    print(f"\n✓ Wrote {count} records to {OUTPUT_FILE}")


if __name__ == '__main__':
    extract_by_date_tab()
