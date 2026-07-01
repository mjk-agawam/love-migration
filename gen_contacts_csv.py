"""Generate contacts.csv for sf data upsert bulk from Ready For Contacts sheet data."""
import csv
import re
import sys

CONTACT_RECORD_TYPE = "012f2000000ww91AAA"  # Household — not used for org contacts directly

# Account name → Salesforce Account ID
ACCOUNT_MAP = {
    '"sparksofjoyprogram"katespadefoundation': '001Ox00001V7Fl0IAF',
    '2026williamtgrant-youthserviceimprovementgrant': '001Ox00001V7FlRIAV',
    'acquisfoundation': '001Ox00001aDMP6IAO',
    'aefoundationcommunitygrant': '001Ox00001V7Fl9IAF',
    'ainsliefoundation': '001Ox00001V7FlpIAF',
    'americaneaglefoundation': '001Ox00001aDMOwIAO',
    'americanexpresscommunitygiving': '001Ox00001V7FlaIAF',
    'amplifyher': '001Ox00001V7FkyIAF',
    'annieecaseyfoundation': '001Ox00001V7FkuIAF',
    'anniee.caseyfoundation': '001Ox00001V7Fl6IAF',
    'arborrising': '001Ox00001aDMPEIA4',
    'bancopopularfoundation': '001Ox00001V7FlFIAV',
    'brooklynorg': '001Ox00001aDMP3IAO',
    'carol&geneludwigfamilyfoundation': '001Ox00001V7FloIAF',
    'ccnsf': '001Ox00001V7FlBIAV',
    'charles&lynnschustermanfamilyphilanthropies': '001Ox00001V7FlcIAF',
    'charlesh.stoutfoundation': '001Ox00001V7FlIIAV',
    'charlesr&winifredrweberfoundation': '001Ox00001V7FllIAF',
    'coachfoundation': '001Ox00001V7FlqIAF',
    'compass(26026p0003)': '001Ox00001V7FlKIAV',
    'firsthorizonfoundation': '001Ox00001aDMPCIA4',
    'firstniagara': '001Ox00001V7FliIAF',
    'footlockerfoundation': '001Ox00001V7FlJIAV',
    'foresthillsstadiumcommunityfund': '001Ox00001aDMPGIA4',
    'frances&edwin': '001Ox00001V7FlTIAV',
    'hispanicfederation2026upliftnewyorkstate': '001Ox00001V7FlMIAV',
    'hydeandwatsonfoundation': '001Ox00001V7FkxIAF',
    'ichigofoundation': '001Ox00001aDMPDIA4',
    'jpmorganchase:thehagedornfund': '001Ox00001V7FlmIAF',
    'kars4kids': '001Ox00001aDMPBIA4',
    'katespade': '001Ox00001V7Fl8IAF',
    'l&bcharitable': '001Ox00001V7Fl5IAF',
    'laurabvoglerfoundation': '001Ox00001aDMOyIAO',
    'lawrencefoundation': '001Ox00001aDMP5IAO',
    'levittfoundation': '001Ox00001V7Fl7IAF',
    'lilyauchinclossfoundation,inc.-humanservicesgrant': '001Ox00001V7Fl2IAF',
    'lilyauchinclossfoundationhumanservicesgrant': '001Ox00001V7FlLIAV',
    'lookingoutfoundation': '001Ox00001V7FkwIAF',
    'lucha(latinunitedcommunityhousingassociation)': '001Ox00001V7FlGIAV',
    'm&tcharitablefund': '001Ox00001V7FlEIAV',
    'mtcharitablefund': '001Ox00001aDMPHIA4',
    'marymulligancharitabletrust': '001Ox00001V7FlOIAV',
    'marysmulligancharitabletrustbankofamerica': '001Ox00001aDMOvIAO',
    'mazdafoundation': '001Ox00001V7FlWIAV',
    'meringofffamilyfoundation': '001Ox00001V7FljIAF',
    "moody'sfoundation": '001Ox00001V7FlfIAF',
    'mothercabrinihealthfoundation': '001Ox00001aDMP2IAO',
    'ms.foundationforwomen': '001Ox00001V7FlbIAF',
    'nationalgrid': '001Ox00001V7FlUIAV',
    'nbcuniverallocalimpactgrant': '001Ox00001aDMP4IAO',
    'newprofit': '001Ox00001aDMP8IAO',
    'newyorkcommunitytrust': '001Ox00001V7FlNIAV',
    'nycserviceyouthleadershipcouncil': '001Ox00001V7Fl4IAF',
    'pinkerton': '001Ox00001V7Fl3IAF',
    'pinkertonfoundation': '001Ox00001V7FkvIAF',
    'resortworldgives': '001Ox00001aDMPFIA4',
    'robinhoodfoundation': '001Ox00001aDMPAIA4',
    'rosennthalfamilyfoundation': '001Ox00001V7Fl1IAF',
    'schottfoundation': '001Ox00001V7FlhIAF',
    'sillsfamilyfoundation': '001Ox00001V7FlnIAF',
    'spectrum': '001Ox00001V7FlPIAV',
    'spectrumdigitaleducationgrant': '001Ox00001aDMOuIAO',
    'theclarkfoundation': '001Ox00001V7FlkIAF',
    'thecricketislandfoundation': '001Ox00001V7FldIAF',
    'thefrancesledwinlcummingsmemorialfund': '001Ox00001aDMOxIAO',
    'thekresgefoundation': '001Ox00001V7FlVIAV',
    'thesillsfamilyfoundation': '001Ox00001V7FlYIAV',
    'theslomo&cindysiivianfoundation': '001Ox00001V7FkzIAF',
    'theslomocindysiivianfoundation': '001Ox00001aDMP7IAO',
    'theslomoandcindysilvianfoundation': '001Ox00001V7FlAIAV',
    'thestarrfoundation': '001Ox00001V7FlZIAV',
    'thirdwavefund(formerlythirdwavefoundation)': '001Ox00001V7FlgIAF',
    'tigerfoundation': '001Ox00001aDMP9IAO',
    'unidosusescaleras': '001Ox00001aDMP1IAO',
    'unidosuspionerasenstem': '001Ox00001aDMP0IAO',
    'viapathfoundation': '001Ox00001aDMOtIAO',
    'viapathimpactgrant': '001Ox00001V7FlQIAV',
    'volger': '001Ox00001V7FlSIAV',
    'voyafinancialfoundation': '001Ox00001V7FleIAF',
    'williamtgrantfoundation-yscg': '001Ox00001V7FlHIAV',
    'williamtgrantfoundationyouthserviceimprovementgrant': '001Ox00001aDMOzIAO',
    'zegarfamilyfoundation': '001Ox00001V7FlXIAV',
}

# Rows from Ready For Contacts (rows 2-31, skipping blank row 32)
# col 0=AccountName, 7=ContactPerson, 8=Title, 9=Email
CONTACT_ROWS = [
    ['Annie E Casey Foundation', '', '', '', '', '', '', 'Allison Gerber                                                                       Ranita Jain                                                                                            Angela Taylor', 'Director for Economic Opportunity                               Program Officer for Economic Opportunity  ', 'agerber@aecf.org                     ATaylor@aecf.org', 'Follow-up with Maria : AUGUST 2025'],
    ['Pinkerton Foundation', '', '', '', '', '', '', 'Jennifer Negron ', '', 'jnegron@pinkertonfdn.org ', 'Follow up in August for new cycle info'],
    ['Looking Out Foundation', '', '', '', '', '', '', 'Catherine Carlile                            Yvonne Murray ', 'Executive Director                       Communications Manager ', 'catherine@lookingoutfoundation.org                                                         yvonne@lookingoutfoundation.org', 'Outreach conducted 4/9                            Followed up 5/15'],
    ['Hyde and Watson Foundation', '', '', '', '', '', '', '', '', 'info@hydeandwatson.org', ''],
    ['Amplify Her', '', '', '', '', '', '', 'Laura Risimini ', '', 'laura@amplifyherfoundation.org', ''],
    ['The Slomo & Cindy Siivian Foundation', '', '', '', '', '', '', 'Daniel Komansky, David Grossman', 'President and Chairman of the Board of Directors, Treasurer and Board Member ', 'dkomansky@silvianfoundation.org, ', ''],
    ['"Sparks of Joy Program" Kate Spade Foundation', '', '', '', '', '', '', 'Claudia has contact info', '', '', ''],
    ['Rosennthal Family Foundation', '', '', '', '', '', '', '', '', 'RFFGrants@alchemizegiving.net', ''],
    ['Lily Auchincloss Foundation, Inc. - Human Services Grant', '', '', '', '', '', '', 'Alexandra A. Herzan\nRossana Martinez \n', 'President and Treasurer                                Manager', 'Alex@lilyauch.org                                  artrossana@gmail.com                               info@lilyauch.org', 'Reached out to Rossana to let her know we are interested in submitting an application (10/10)'],
    ['Pinkerton ', '', '', '', '', '', '', '', '', '', ''],
    ['NYC Service Youth Leadership Council', '', '', '', '', '', '', '', '', '', ''],
    ['L&B Charitable ', '', '', '', '', '', '', 'Peter Marks', 'Executive Director', 'pmarks@thelbfoundation.org', 'Meeting 11/14'],
    ['Annie E. Casey Foundation', '', '', '', '', '', '', 'Marcella Hurtado', 'Senior Associate', 'MHurtadoGomez@aecf.org', 'LOI submitted: 4/16'],
    ['Levitt Foundation', '', '', '', '', '', '', 'Hilda Polanco\nMegan Tomey', 'L.O.V.E. Board\nConsultant of TCC Group', 'LevittFoundation@tccgrp.com', ''],
    ['Kate Spade ', '', '', '', '', '', '', 'Jessica Viets', 'Senior Manager, Global Social ImpactSecretary of the Kate Spade New York Foundation', 'jviets@katespade.com', 'Meeting 5/14'],
    ['AE Foundation Community Grant', '', '', '', '', '', '', 'Judy Meehan;\nMarisa Baldwin', 'President, as needed; \nPresident, as needed', 'grants@ae.com; \nmeehanj@ae.com; \nbaldwinm@ae.com', 'JC 6/24'],
    ['The Slomo and Cindy Silvian Foundation', '', '', '', '', '', '', 'Daniel S. Komansky', 'President', '', ''],
    ['CCNSF', '', '', '', '', '', '', 'ALMIRCA SANTIAGO', '', 'ASANTIAGO@HISPANICFEDERATION.ORG', 'NG 10/1'],
    ['UnidosUS – Pioneras en STEM', '', '', '', '', '', '', '—', '—', '—', ''],
    ['UnidosUS – Escaleras', '', '', '', '', '', '', '—', '—', '—', ''],
    ['M&T Charitable Fund', '', '', '', '', '', '', 'Ade Escayg', '', 'aescayg@mtb.com', 'NG 9/29'],
    ['Banco Popular Foundation', '', '', '', '', '', '', '', '', '', ''],
    ['LUCHA (Latin United Community Housing Association)', '', '', '', '', '', '', 'Lincoln Stannard; Lillian Bui', 'Co-Executive Directors', 'lstannard@lucha.org; lbui@associationhouse.org', ''],
    ['William T Grant Foundation - YSCG', '', '', '', '', '', '', 'Selina Lee', 'Grants Administrator', 'slee@wtgrantfdn.org', ''],
    ['Charles H. Stout Foundation', '', '', '', '', '', '', 'Richard M. Stout', 'President', 'richardmstout@earthlink.net', 'JC 6/9'],
    ['Foot Locker Foundation', '', '', '', '', '', '', '', '', '', ''],
    ['LUCHA (Latin United Community Housing Association)', '', '', '', '', '', '', 'Lincoln Stannard; Lillian Bui', 'Co-Executive Directors', 'lstannard@lucha.org; lbui@associationhouse.org', ''],
    ['COMPASS (26026P0003)', '', '', '', '', '', '', 'Department of Youth & Community Development (DYCD) — COMPASS / PASSPort support: MOCS Service Desk (PASSPort technical help & RFx system): https://mocssupport.atlassian.net/servicedesk/customer/portal/8; MOCS Service Desk email: MOCSReply@servicedesk.mocs.nyc.gov. DYCD Fiscal/contract help (Budget & Finance): BudgetandFinanceHelp@dycd.nyc.gov. Incident reporting / DYCD program contact: incidentreports@dycd.nyc.gov.', 'n/a (agency / helpdesk entries)', 'Bilingual Welcome Events; consent drives; university mentor pipelines; family workshops.', ''],
    ['COMPASS (26026P0003)', '', '', '', '', '', '', 'Department of Youth & Community Development (DYCD) — COMPASS / PASSPort support: MOCS Service Desk (PASSPort tech): https://mocssupport.atlassian.net/servicedesk/customer/portal/8; MOCS email MOCSReply@servicedesk.mocs.nyc.gov. DYCD Budget/Finance: BudgetandFinanceHelp@dycd.nyc.gov. Incident reports/program email: incidentreports@dycd.nyc.gov.', 'n/a', 'Bilingual Welcome Events; consent drives; targeted outreach for newly-arrived families at Academy for New Americans; university mentor pipelines.', ''],
    ['COMPASS (26026P0003)', '', '', '', '', '', '', 'Department of Youth & Community Development (DYCD) — COMPASS / PASSPort support: MOCS Service Desk: https://mocssupport.atlassian.net/servicedesk/customer/portal/8; email MOCSReply@servicedesk.mocs.nyc.gov. DYCD Budget/Finance: BudgetandFinanceHelp@dycd.nyc.gov. Incident reports / program: incidentreports@dycd.nyc.gov.', 'n/a', 'Bilingual Welcome Events; consent drives; layered staffing model described; per-site budgets and combined total provided in the Manhattan-07 proposal.', ''],
    ['Lily Auchincloss Foundation – Human Services Grant', '', '', '', '', '', '', '—', '—', '—', 'Not submitted'],
    ['Hispanic Federation 2026 UPLift New York State', '', '', '', '', '', '', 'Gonzalo Loayza', '', 'gloayza@hispanicfederation.org', ''],
    ['New York Community Trust', '', '', '', '', '', '', 'Leigh C. Ross ', 'Program Director, Gender Equity, Early Childhood, and Arts Education', 'lcr@nyct-cfi.org | ', ''],
    ['Mary Mulligan Charitable Trust ', '', '', '', '', '', '', '', '', '', ''],
    ['Spectrum', '', '', '', '', '', '', '', '', '', ''],
    ['ViaPath Impact Grant ', '', '', '', '', '', '', '', '', '', ''],
    ['2026 William T Grant - Youth Service Improvement Grant', '', '', '', '', '', '', 'Selina Lee', 'Grants Adminisrator ', 'slee@wtgrantfdn.org', ''],
    ['Volger ', '', '', '', '', '', '', '', '', '', ''],
]

EM_DASH = '—'
EN_DASH = '–'


def is_blank(v):
    s = str(v).strip() if v else ''
    return s in ('', EM_DASH, EN_DASH, '-', 'N/A', '#ERROR!')


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s


_SLUGGED_MAP = None

def acct_id(name):
    """Look up account ID by name slug (both query and keys are slugified)."""
    global _SLUGGED_MAP
    if _SLUGGED_MAP is None:
        _SLUGGED_MAP = {slugify(k): v for k, v in ACCOUNT_MAP.items()}
    slug = slugify(name)
    aid = _SLUGGED_MAP.get(slug)
    if not aid:
        # prefix fallback
        for k, v in _SLUGGED_MAP.items():
            if k[:25] == slug[:25]:
                return v
    return aid


def split_multi(val, sep_pattern=r'[,;\n]+'):
    """Split a multi-value string into a list, cleaning whitespace.
    Also splits on 3+ consecutive spaces (padded multi-value cells)."""
    if is_blank(val):
        return []
    s = str(val)
    # Normalize: replace 3+ spaces with a delimiter
    s = re.sub(r' {3,}', '\n', s)
    parts = re.split(sep_pattern, s)
    return [p.strip() for p in parts if p.strip() and not is_blank(p.strip())]


def make_ext_id(acct_name, first, last):
    return f"contact_{slugify(acct_name)}_{slugify(first)}_{slugify(last)}"


out_path = '/Users/mikeknight/Projects/love-migration/contacts.csv'
fields = [
    'Contact_External_ID__c', 'AccountId', 'FirstName', 'LastName',
    'Title', 'Email',
]

seen_ext_ids = {}
written = 0
skipped = 0

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()

    for row in CONTACT_ROWS:
        acct_name = row[0].strip()
        contact_raw = row[7] if len(row) > 7 else ''
        title_raw = row[8] if len(row) > 8 else ''
        email_raw = row[9] if len(row) > 9 else ''

        if is_blank(contact_raw):
            continue

        # Skip COMPASS rows (agency helpdesk entries, not real contacts)
        if 'COMPASS' in acct_name or 'DYCD' in str(contact_raw):
            continue

        # Skip "Claudia has contact info" placeholder
        if 'claudia' in str(contact_raw).lower() and 'info' in str(contact_raw).lower():
            continue

        aid = acct_id(acct_name)
        if not aid:
            print(f"WARNING: no account ID for '{acct_name}'", file=sys.stderr)

        names = split_multi(contact_raw)
        titles = split_multi(title_raw, r'[;\n]+')
        emails = split_multi(email_raw, r'[;\n|,]+')

        for i, full_name in enumerate(names):
            parts = full_name.split()
            if not parts:
                continue
            first = parts[0]
            last = ' '.join(parts[1:]) if len(parts) > 1 else ''

            title = titles[i] if i < len(titles) else (titles[0] if titles else '')
            email = emails[i] if i < len(emails) else (emails[0] if emails else '')
            # Clean email
            email = email.strip().rstrip('|').strip()
            if is_blank(email) or '@' not in email:
                email = ''

            ext_id = make_ext_id(acct_name, first, last)
            # Handle duplicates
            if ext_id in seen_ext_ids:
                seen_ext_ids[ext_id] += 1
                ext_id = f"{ext_id}_{seen_ext_ids[ext_id]}"
            else:
                seen_ext_ids[ext_id] = 1

            if not last:
                # Single-name entry — use as last name
                last = first
                first = ''

            w.writerow({
                'Contact_External_ID__c': ext_id,
                'AccountId': aid or '',
                'FirstName': first,
                'LastName': last,
                'Title': title[:255] if title else '',
                'Email': email,
            })
            written += 1

print(f"Wrote {written} contacts to {out_path}", file=sys.stderr)
