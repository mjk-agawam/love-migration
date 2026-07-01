"""Generate opportunities.csv for sf data import bulk from accounts data."""
import csv
import re
import sys

# Account External ID → Salesforce Account ID (from our upsert)
# We'll build from the accounts.csv + query results
ACCT_EXT_TO_ID = {
    'hispanicfederation2026upliftnewyorkstate': '001Ox00001V7FlMIAV',
    'viapathfoundation': '001Ox00001aDMOtIAO',
    'spectrumdigitaleducationgrant': '001Ox00001aDMOuIAO',
    'marysmulligancharitabletrustbankofamerica': '001Ox00001aDMOvIAO',
    'americaneaglefoundation': '001Ox00001aDMOwIAO',
    'thefrancesledwinlcummingsmemorialfund': '001Ox00001aDMOxIAO',
    'laurabvoglerfoundation': '001Ox00001aDMOyIAO',
    'williamtgrantfoundationyouthserviceimprovementgrant': '001Ox00001aDMOzIAO',
    'unidosuspionerasenstem': '001Ox00001aDMP0IAO',
    'unidosusescaleras': '001Ox00001aDMP1IAO',
    'mothercabrinihealthfoundation': '001Ox00001aDMP2IAO',
    'brooklynorg': '001Ox00001aDMP3IAO',
    'nbcuniverallocalimpactgrant': '001Ox00001aDMP4IAO',
    'lawrencefoundation': '001Ox00001aDMP5IAO',
    'acquisfoundation': '001Ox00001aDMP6IAO',
    'theslomocindysiivianfoundation': '001Ox00001aDMP7IAO',
    'newprofit': '001Ox00001aDMP8IAO',
    'tigerfoundation': '001Ox00001aDMP9IAO',
    'sillsfamilyfoundation': '001Ox00001V7FlnIAF',
    'robinhoodfoundation': '001Ox00001aDMPAIA4',
    'kars4kids': '001Ox00001aDMPBIA4',
    'firsthorizonfoundation': '001Ox00001aDMPCIA4',
    'ichigofoundation': '001Ox00001aDMPDIA4',
    'arborrising': '001Ox00001aDMPEIA4',
    'resortworldgives': '001Ox00001aDMPFIA4',
    'foresthillsstadiumcommunityfund': '001Ox00001aDMPGIA4',
    'ccnsf': '001Ox00001V7FlBIAV',
    'mtcharitablefund': '001Ox00001aDMPHIA4',
    'bancopopularfoundation': '001Ox00001V7FlFIAV',
}

# (acct_name, ext_id, grant_amount_text, due_date_text, submission_status, acct_info)
ACCT_ROWS = [
    ('Hispanic Federation 2026 UPLift New York State', 'hispanicfederation2026upliftnewyorkstate', '', 'February 6, 2026', 'Submitted 2/5/2026', 'Portal'),
    ('ViaPath Foundation', 'viapathfoundation', 'cap of $50,000 over a three-year period', 'February 20, 2026', 'Submitted 2/20/2026', 'ViaPath Foundation'),
    ('Spectrum Digital Education Grant', 'spectrumdigitaleducationgrant', '$2,500 - $50,000', 'February 27, 2026', 'Submitted 2/27/2026', 'Spectrum Digital Education Grant'),
    ('Mary S. Mulligan Charitable Trust (Bank of America)', 'marysmulligancharitabletrustbankofamerica', '$2,000 up to about $36,150', 'March 1 ; September 1', 'Submitted 3/1/2026', 'Mary Mulligan Portal'),
    ('American Eagle Foundation', 'americaneaglefoundation', '$5,000 - $15,000', 'March 2, 2026; August 10, 2026', 'Submitted 3/2/2026', 'American Eagle Portal'),
    ('The Frances L. & Edwin L. Cummings Memorial Fund', 'thefrancesledwinlcummingsmemorialfund', 'Average - $70,000', '4/1/2026; 10/1/2026', 'Submitted 4/1/2026', 'Frances & Edwin Fund'),
    ('Laura B. Vogler Foundation', 'laurabvoglerfoundation', '$3,000–$4,000', 'July 1; October 1', 'Submitted 4/1/2026', 'Laura B. Volger Application'),
    ('William T. Grant Foundation (Youth Service Improvement Grant)', 'williamtgrantfoundationyouthserviceimprovementgrant', '$25,000', 'April 1, 2026', 'Submitted 4/1/2026', 'William Grant Application Portal'),
    ('UnidosUS – Pioneras en STEM', 'unidosuspionerasenstem', '$20,000', 'April 1', 'Submitted 4/1', 'Portal'),
    ('UnidosUS – Escaleras', 'unidosusescaleras', '$40,000', 'April 1', 'Submitted 4/1', 'Portal'),
    ('Mother Cabrini Health Foundation', 'mothercabrinihealthfoundation', '$75,000+', '2026 TBD', 'Submitted 4/23/2026', 'Mother Cabrini Health Portal'),
    ('Brooklyn Org', 'brooklynorg', '', 'September 30th', 'Submitted 4/23/2026', 'Brooklyn Org Portal'),
    ('NBCUniveral Local Impact Grant', 'nbcuniverallocalimpactgrant', 'No more than 30% of reported expenses', 'April 24, 2026', 'Submitted 4/24/2026', 'NBCUniversal Portal'),
    ('Lawrence Foundation', 'lawrencefoundation', '$5,000 - $10,000', 'April 30; October 31.', 'Submitted 4/30/2026', 'Lawrence Application'),
    ('Acquis Foundation', 'acquisfoundation', '$46,142', 'June 11', 'Submitted 4/30/2026', 'RFP'),
    ('The Slomo & Cindy Siivian Foundation', 'theslomocindysiivianfoundation', '$20,000', '6/1/2026', 'Submitted 5/15', 'Portal'),
    ('New Profit', 'newprofit', '$110,000 (100k for organization; 10k for leadership development)', 'May 26', 'Submitted 5/22/2026', 'Discovery Form'),
    ('Tiger Foundation', 'tigerfoundation', '$50,000 - $300,000 (Average $200,000)', 'Rolling', 'Submitted 5/26/2026', 'Tiger Foundation Portal'),
    ('Sills Family Foundation', 'sillsfamilyfoundation', '$10,000 to $25,000', 'N/A', 'LOI Submitted', 'No Application Posted'),
    ('Robin Hood Foundation', 'robinhoodfoundation', '$100,000 - $1,600,000', 'Open year-round', 'Submitted 4/10/2026', 'Robinhood Grant Application'),
    ('Kars4Kids', 'kars4kids', '$500 to $2,000', 'Open year-round', 'Submitted', 'Kars4Kids Application'),
    ('First Horizon Foundation', 'firsthorizonfoundation', '$5,000 to $25,000', 'Rolling', 'In Progress', 'First Horizon Application'),
    ('Ichigo Foundation', 'ichigofoundation', '$25,000-$250,000', 'Rolling', 'In Progress', 'Ichigo LOI'),
    ('Arbor Rising', 'arborrising', '$125,000', 'June 9', 'In Progress', 'Arbor LOI'),
    ('Resort World Gives', 'resortworldgives', '$50,000', 'November 1', 'In Progress', 'Resort World Portal'),
    ('Forest Hills Stadium Community Fund', 'foresthillsstadiumcommunityfund', 'Tier 1: up to $5000\nTier 2: $5000 - $10,000\nTier 3: $10,000 - $15,000', 'Rolling', 'In Progress', 'Forest Hills Application'),
    ('CCNSF', 'ccnsf', '$45,000', 'October 17th', '', 'Portal'),
    ('M&T Charitable Fund', 'mtcharitablefund', 'Varies', 'October 31st', '', 'Portal'),
    ('Banco Popular Foundation', 'bancopopularfoundation', '$10,000', 'August 31st, 2025', '', 'Portal'),
]


def map_stage(status):
    s = status.lower().strip()
    if not s:
        return 'Prospecting'
    if 'loi submitted' in s:
        return 'LOI Submitted'
    if s.startswith('submitted'):
        return 'Application Submitted'
    if 'in progress' in s:
        return 'Prospecting'
    if s.startswith('ng') or 'declined' in s:
        return 'Closed Lost'
    return 'Prospecting'


def parse_close_date(due_date_text):
    """Extract first date-like value; default to 2026-12-31."""
    if not due_date_text:
        return '2026-12-31'
    s = due_date_text.strip()
    if s in ('Rolling', 'Open year-round', 'N/A', '2026 TBD', 'Varies'):
        return '2026-12-31'

    # Try "Month Day, Year"
    m = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})', s, re.I)
    if m:
        months = {'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06',
                  'july':'07','august':'08','september':'09','october':'10','november':'11','december':'12'}
        mo = months[m.group(1).lower()]
        return f"{m.group(3)}-{mo}-{int(m.group(2)):02d}"

    # Try M/D/YYYY
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"

    # Try "Month Day" without year — assume 2026
    m = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})', s, re.I)
    if m:
        months = {'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06',
                  'july':'07','august':'08','september':'09','october':'10','november':'11','december':'12'}
        mo = months[m.group(1).lower()]
        return f"2026-{mo}-{int(m.group(2)):02d}"

    return '2026-12-31'


def extract_amount(grant_text):
    """Extract first dollar amount as a number."""
    if not grant_text:
        return ''
    m = re.search(r'\$\s*([\d,]+)', grant_text)
    if m:
        return m.group(1).replace(',', '')
    return ''


out_path = '/Users/mikeknight/Projects/love-migration/opportunities.csv'
fields = ['Name', 'AccountId', 'StageName', 'CloseDate', 'Amount', 'Description']

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    count = 0
    for name, ext_id, grant_amt, due_date, status, acct_info in ACCT_ROWS:
        aid = ACCT_EXT_TO_ID.get(ext_id)
        if not aid:
            print(f"WARNING: no account ID for {ext_id}", file=sys.stderr)
            continue
        stage = map_stage(status)
        close_date = parse_close_date(due_date)
        amount = extract_amount(grant_amt)
        # Opportunity name: "Account Name Grant Application"
        opp_name = f"{name} Grant Application"[:120]
        desc = f"Grant range: {grant_amt}" if grant_amt else ''
        w.writerow({
            'Name': opp_name,
            'AccountId': aid,
            'StageName': stage,
            'CloseDate': close_date,
            'Amount': amount,
            'Description': desc[:255],
        })
        count += 1

print(f"Wrote {count} opportunities to {out_path}", file=sys.stderr)
