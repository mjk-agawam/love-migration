"""Generate individual donor CSVs for sf bulk load.

Outputs:
  indiv_accounts.csv   — upsert with Account_External_ID__c
  indiv_contacts.csv   — plain import (no ext ID configured)
  indiv_opps.csv       — plain import (no ext ID configured)
"""
import csv
import re
import sys
import unicodedata

PROJ = '/Users/mikeknight/Projects/love-migration'
RT_HOUSEHOLD = '012f2000000ww91AAA'


def slugify(text):
    t = unicodedata.normalize('NFKD', str(text).strip())
    t = t.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]', '', t.lower())


def clean_amount(v):
    v = str(v).strip()
    if not v or v in ('-', '—', '–'):
        return ''
    v = re.sub(r'[$,\s]', '', v)
    try:
        f = float(v)
        return str(int(f)) if f > 0 else ''
    except ValueError:
        return ''


def make_ext_id(prefix, first, last, seen):
    base = f"indiv_{prefix}_{slugify(first)}{slugify(last)}"
    n = seen.get(base, 0) + 1
    seen[base] = n
    return base if n == 1 else f"{base}_{n}"


# Row format: (first, last, email, [(year, amount_str), ...])
# Dash/zero amounts excluded. Email already resolved (W-col first, C-col fallback).
# '' email = no email on file.

BOARD = [  # years present: 2021-2026
    ('Michelle', 'Warra', 'michellewarra@gmail.com', [(2025,'$2,000'),(2024,'$2,250'),(2023,'$2,400'),(2022,'$1,800'),(2021,'$300')]),
    ('Barbara', 'Orisio', 'borisio1112@gmail.com', [(2025,'$675'),(2024,'$925'),(2023,'$900'),(2022,'$1,300')]),
    ('Wendy', 'Reynoso', 'wareynoso@gmail.com', [(2024,'$200'),(2023,'$490'),(2022,'$1,040'),(2021,'$150')]),
    ('Danna', 'Deblasio', 'deblasio.danna@gmail.com', [(2025,'$250'),(2024,'$400'),(2022,'$500'),(2021,'$600')]),
    ('Anjanette', 'Cabrera', 'acabrera@constangy.com', [(2026,'$400'),(2025,'$1,200'),(2024,'$1,000'),(2023,'$1,100')]),
    ('Diana', 'Gasperoni', 'dianamgasperoni@gmail.com', [(2026,'$500'),(2025,'$625'),(2021,'$600')]),
    ('Shireesha', 'Nethi', 'shireesharavi@yahoo.com', []),
]

AMIGOS = [  # years present: 2022-2026
    ('Cecilia', 'Garza', 'garzacecy@gmail.com', [(2026,'$1,000'),(2025,'$4,540'),(2024,'$3,120')]),
    ('Christian', 'Audi', '', [(2026,'$250')]),
    ('Hazel', 'Guzman', 'hguzman@carmellhill.net', [(2025,'$500')]),
    ('David', 'Smith', 'david.s.smith@pfizer.com', [(2025,'$1,000'),(2024,'$1,000'),(2023,'$1,000'),(2022,'$450')]),
    ('Noel', 'Borbon', 'noel.borbon25@gmail.com', [(2025,'$250')]),
    ('Diana', 'Plazas-Trowbridge', 'diana.plazas@marriott.com', [(2025,'$500')]),
    ('Suhailey', 'Nunez', 'suhailey@bewellpsychotherapy.com', [(2025,'$538')]),
    ('Elizabeth', 'Faler', 'elizabeth.faler@editionhotels.com', [(2025,'$400')]),
    ('Ignaura', 'Tejada', 'ignaura@gmail.com', [(2025,'$396')]),
    ('Andreina', 'Gonzalez', 'andreina@lovementoring.org', [(2025,'$200')]),
    ('Cristina', 'Pacheco', 'cristina_pacheco@glic.com', [(2025,'$563')]),
    ('Luis', 'Alonso', '', [(2025,'$200')]),
    ('Tomas', 'Colloca', 'bargallo@google.com', [(2025,'$225')]),
    ('Christine', 'Switzer', 'christine@themonarchfoundation.org', [(2025,'$1,270')]),
    ('Irais Daniela', 'Galvez', 'iraisgalvez@google.com', [(2025,'$400')]),
    # row 16 skipped: both names "Not Shared by Donor"
    ('Timothy', 'Morales', 'timmorales@google.com', [(2025,'$400')]),
    ('Patricia', 'Sousa', 'pattisousasterling@gmail.com', [(2024,'$805')]),
    ('Orit', 'Goldring', 'oritgoldring@gmail.com', [(2024,'$670')]),
    ('John', 'Jurcisin', 'johnj10022@aol.com', [(2023,'$1,000')]),
    ('Christian', 'Audi', 'caudiw@gmail.com', [(2024,'$1,000'),(2023,'$1,000'),(2022,'$1,400')]),
    ('Lawrence', 'Prybylski', 'lawrence.prybylski@eyg.ey.com', [(2024,'$500'),(2023,'$500'),(2022,'$500')]),
    ('Nicolas', 'Vincent', 'nicolqs@gmail.com', [(2024,'$250')]),
    ('Denise', 'Sibrian', 'denise.sibrian@macys.com', [(2024,'$250')]),
    ('Neysa', 'Alsina', 'neysairis@gmail.com', [(2023,'$500')]),
    ('Elena', 'Paraskevas-Thadani', 'ept@eptlegal.com', [(2023,'$400'),(2022,'$1,000')]),
    ('Zully', 'Avellaneda', 'zullyave@yahoo.com', [(2024,'$350'),(2023,'$400')]),
    ('Felipe', 'Espinosa', 'felipeespi@hotmail.com', []),
    ('Paola', 'Espinosa', 'paolaespinosab@gmail.com', [(2024,'$200'),(2023,'$200'),(2022,'$250')]),
    ('Jane', 'Nadler', 'janenadler@gmail.com', [(2023,'$200'),(2022,'$200')]),
    ('Catalina', 'Hodenfield', 'chodenfield@wpfund.org', [(2024,'$300')]),
    ('Christine', 'Hogan', 'christinehogan1@gmail.com', [(2024,'$250')]),
    ('Geidy', 'Perez', 'geidy.perez@gmail.com', [(2024,'$250')]),
    ('Valerie', 'Aloe', 'valeriaaloe@gmail.com', [(2023,'$350')]),
    ('Edwin', 'Pisani', 'edwinjpisani@gmail.com', [(2023,'$250')]),
    ('Kelli-Anne', 'Cerini', 'kacerini@cerinicpa.com', [(2023,'$250')]),
    ('Vianny', 'Pichardo', 'vianny.pichardo@gmail.com', [(2023,'$250')]),
    ('Elisa', 'Istueta', 'eistueta@gmail.com', []),
    ('Lisette', 'Nieves', 'lnieves01@gmail.com', []),
    ('Mathew', 'Malloy', 'malloy.matthewh@gmail.com', []),
    ('Michael', 'Woloz', 'mwoloz@cmw-newyork.com', []),
    ('Michael', 'Peguero', 'mikepeguero@gmail.com', [(2022,'$250')]),
    ('Stephanie', 'Perez', 'sperez618@yahoo.com', [(2022,'$300')]),
    ('Alicia', 'Menendez', 'alicia.menendez@gmail.com', [(2022,'$400')]),
    ('Charlotte', 'Castillo', 'charlotte@poderistas.com', [(2022,'$400')]),
    ('Crystal', 'Stoll Alvarez', 'crystalalvarez@google.com', [(2022,'$400')]),
    ('Alex', 'Patterson', 'alexseville@gmail.com', [(2023,'$200')]),
]

CAMPANEROS = [  # years present: 2021-2026
    ('James', 'Abro', '', [(2025,'$97')]),
    ('Casey', 'Blake', '', [(2025,'$75')]),
    ('Alicia', 'Sierra', '', [(2025,'$110')]),
    ('Clara', 'Rapuzzi', 'cid.r1000@gmail.com', [(2025,'$100'),(2023,'$100'),(2021,'$150')]),
    ('Mandy', 'Chua', 'mandy.hj.chua@gmail.com', [(2025,'$100')]),
    ('Tania', 'Galarza', 'tgalarza74@gmail.com', [(2025,'$100')]),
    ('Fiona', 'Brandman', 'fbrandman16@gmail.com', [(2025,'$98')]),
    ('Janaina Isa', 'Poeta Frey', 'janainaf@google.com', [(2025,'$160')]),
    ('Neida Carla', 'Costa de Freitas', '', [(2025,'$75')]),
    ('Ricardo', 'Camarena Bailon', 'camarenabailon@google.com', [(2025,'$100')]),
    ('Paola', 'Arias', 'paola.arias@pfizer.com', [(2024,'$100')]),
    ('Christopher', 'Hogerty', 'chogerty@microsoft.com', [(2024,'$150')]),
    ('Beth', 'Diamond', 'bdiamond@outlook.com', [(2024,'$100')]),
    ('Cheryl', 'Taruc', 'cheryltaruc@gmail.com', [(2023,'$150')]),
    ('Diana', 'Hamar', 'diana.hamar@ros.com', [(2023,'$100'),(2022,'$100')]),
    ('Ivy', 'Barnwell', 'inbarnwell@yahoo.com', [(2023,'$100')]),
    ('Yancy', 'Garrido', 'ygarrido@clarkest.com', []),
    ('Alex', 'Mastroianni', 'alex.mastroianni@macys.com', []),
    ('Ana', 'Oliveira', 'aoliveira@nywf.org', []),
    ('Angela', 'Diaz', 'angela.diaz@mountsinai.org', []),
    ('Camille', 'Emeagwali', 'cemeagwali@nywf.org', []),
    ('Damely', 'Tineo', 'dtb1207@hotmail.com', []),
    ('Elsa Marie', 'Collins', 'elsa@theideateur.com', []),
    ('Helen', 'Arteaga', 'arteagah@nychhc.org', []),
    ('Hilda', 'Polanco', 'hpolanco@fmaonline.net', []),
    ('Joyce', 'Sanchez', 'joyce.sanchez@macys.com', []),
    ('Juan', 'Medrano', 'juanmedra@microsoft.com', []),
    ('Kenya', 'Jiu', 'bkjiu@yahoo.com', []),
    ('Kourtney', 'Cockrell', 'kourtney.cockrell@jpmchase.com', []),
    ('Lailany', 'Sierra', 'lailany.sierra@gmail.com', []),
    ('Mayra', 'Linares-Garcia', 'mayralinares@libertycoke.com', []),
    ('Melissa', 'Vargas', 'melissa@philanthropytogether.org', []),
    ('Rosevelie', 'Morales', 'rosevelie.marquezmorales@hoganlovells.com', [(2022,'$200')]),
    ('Shireesha', 'Nethi', 'co.boiny@bankofindia.co.in', []),
    ('Abdul', 'Rad', 'rad.abdul@gmail.com', [(2022,'$100')]),
    ('Abhisek', 'Patra', 'abhisek.patra@bankofindia.co.in', []),
    ('Adam', 'Colon', 'adam.colon22@gmail.com', [(2022,'$200'),(2021,'$150')]),
    ('Adriana', 'Londono', 'alondono@nywf.org', [(2022,'$100')]),
    ('Albert', 'Barrueco', 'albarrueco@firstquality.com', [(2022,'$200')]),
    ('Alejandra', 'Silguero', 'alejandra.silguero@gmmb.com', []),
    ('Alfred', 'Ojukwu', 'alojukwu@microsoft.com', [(2022,'$150')]),
    ('Alison', 'Formidoni', 'ardembe@gmail.com', [(2022,'$200')]),
    ('Alizabeth', 'Acevedo', 'lizash13@gmail.com', []),
    ('Alizanette', 'Rodriguez', 'alizanette.rodriguez@verizonwireless.com', [(2022,'$200')]),
    ('Amanda', 'Clarke', 'amclarke@microsoft.com', [(2022,'$150')]),
    ('Amanda', 'Maximin', 'amanda.maximin@pepsico.com', []),
    ('Ana', 'Almanzar', 'ana.almanzar@cabrinihealth.org', []),
    ('Ana Maria', 'Tejada', 'atejada@kdvlaw.com', [(2022,'$200')]),
    ('Andrea', 'Riquelme', 'ariquelme@libertycoke.com', []),
    ('Anshuman', 'Tewari', 'anshuman.tewari2@bankofindia.co.in', []),
    ('Antonia', 'Diaz', 'tonid02@yahoo.com', []),
    ('Arelia', 'Tavaras', 'arelia@nybusinesslicensing.com', []),
    ('Arnaldo', 'Polanco', 'arnaldo.polanco@macys.com', []),
    ('Ashis K', 'Semwa', 'ashis.semwal@bankofindia.co.in', []),
    ('Ashis Kumar', 'Semwal', 'ashis.semwal@bankofindia.co.in', []),
    ('Ashleigh', 'Carney', 'ashleigh.carney@macys.com', []),
    ('Ashley', 'Morse', 'amorse@nywf.org', []),
    ('Ashutosh Kumar', 'Rai', 'ashutosh.rai@bankofindia.co.in', []),
    ('Aydee', 'Trimino', 'triminoa@nychhc.org', []),
    ('Azadeh', 'Khalili', 'akhalili@nywf.org', []),
    ('Basilisa', 'Canto', 'cantob@nychhc.org', []),
    ('Bernadette', 'Beekman', 'bernadette@legal-innovators.com', []),
    ('Brandon', 'Clark', 'brcla@microsoft.com', [(2022,'$163')]),
    ('Carlina', 'Rivera', 'clrivera@council.nyc.gov', []),
    ('Carmen', 'Diaz-Malvido', 'cdiazmalvido@nyaspira.org', []),
    ('Carol', 'Castro', 'ccastro1110@yahoo.com', []),
    ('Carol', 'White', 'whitec@nychhc.org', []),
    ('Carolina', 'Walther-Meade', 'cwalther-meade@milbank.com', [(2022,'$200')]),
    ('Carolina', 'Guardiola Romo', 'carolina@weareallhuman.org', []),
    ('Chadwick', 'Devlin', 'csdev023@gmail.com', [(2022,'$100')]),
    ('Chander Mohan', 'Kumra', 'chander.kumra@bankofindia.co.in', []),
    ('Chanelle', 'Figueroa', 'chanellefigueroa@gmail.com', []),
    ('Chelsea', 'De Jesus', 'chelsea.dejesus@exec.ny.gov', []),
    ('Christine', "O'Donnell", 'christine.l.odonnell@bofa.com', []),
    ('Christine', 'Augenbraun', 'chrismaugen@gmail.com', []),
    ('Cielo', 'Nieves', 'lnieves01@gmail.com', [(2021,'$150')]),
    ('Constantine', 'Conner Kechriotis', 'constantine.kechriotis@ey.com', []),
    ('Cyrus', 'Zavieh', 'zaviehc@nychhc.org', []),
    ('Daisy', 'Perez', 'dperez@healthsolutions.org', []),
    ('Daniel', 'Brown', 'dtbrown@queensda.org', []),
    ('Daniella', 'Trimble', 'grants@ae.com', []),
    ('David', 'Guzman', 'dguzman392@aol.com', [(2021,'$150')]),
    ('Diana', 'Soto', 'diana.soto@bnymellon.com', []),
    ('Diana A', 'Perez', 'diana.a.perez@bnymellon.com', []),
    ('Dilip', 'Kumar', 'dknyc28@gmail.com', [(2021,'$150')]),
    ('Dolly', 'Martinez', 'dolly.martinez@cuny.edu', []),
    ('Dominique-Laura', 'Pierce', 'dpierce@nywf.org', []),
    ('Dorie', 'Gladney', 'dogladne@microsoft.com', [(2022,'$150')]),
    ('Dorys Gabriella', 'Mayorga', 'mayorgado@metroplus.org', []),
    ('Edelweis', 'Avalos', 'edelweissava@gmail.com', [(2022,'$200')]),
    ('Elizabeth', 'Colman', 'ecolman@libertycoke.com', []),
    ('Emily', 'Kadar', 'emily.kadar@exec.ny.gov', []),
    ('Erica', 'Mosley', 'erica.mosely@macys.com', []),
    ('Ezana', 'Tadese', 'ezanatadese@microsoft.com', [(2022,'$150')]),
    ('Felix', 'Rodriguez', 'felix.rodriguez@cuny.edu', []),
    ('Fermin', 'Espinosa', 'ferminespinosa72@gmail.com', []),
    ('Fiona', 'Montouth', 'fiona.byfield@macys.com', []),
    ('Florencia', 'Lauria', 'florencia.lauria@ey.com', []),
    ('Frank', 'Palma Gomez', 'fpg@google.com', [(2022,'$100')]),
]

ALIADOS = [  # years present: 2022-2026
    ('Balveer Singh', 'Rathore', 'balveer.rathore@bankofindia.co.in', [(2026,'$50'),(2025,'$50')]),
    ('Rajiv', 'Kachappilly', '', [(2026,'$38')]),
    ('Kathleen', 'Malpica', 'kathleen.malpica3@t-mobile.com', [(2026,'$24'),(2025,'$29'),(2024,'$45')]),
    ('Rofiat', 'Olasunkanmi', '', [(2026,'$50')]),
    ('Michael', 'Knight', 'mikeknight@salesforce.com', [(2025,'$50')]),
    ('Victoria', 'Gobbo', '', [(2025,'$17')]),
    ('Johanna', 'Ospina', '', [(2025,'$19')]),
    ('Omari', 'Holtz', 'omariholtz@microsoft.com', [(2025,'$50')]),
    ('Simon', 'Gibson', 'simonmorph@gmail.com', [(2025,'$50')]),
    ('Lindsay', 'Marnet', 'lindsayemarnet@gmail.com', [(2025,'$50')]),
    ('Rush', 'Urschel', 'rush@seksomethinggood.com', [(2025,'$10')]),
    ('Jasmine', 'Rodriguez', 'jarodrig@microsoft.com', [(2025,'$50')]),
    ('George', 'Kesse', 'georgekesse@microsoft.com', [(2025,'$50')]),
    ('Odalys', 'Ramos', '', [(2025,'$24'),(2024,'$45')]),
    ('Maria', 'Ferrandina', '', [(2025,'$29'),(2024,'$70')]),
    ('Karen', 'Drezner', '', [(2025,'$25')]),
    ('Sayon', 'Camara', '', [(2025,'$20')]),
    ('Steven', 'Davenport', '', [(2025,'$3')]),
    ('Justin', 'Bourguignon', 'justinbb@google.com', [(2025,'$50')]),
    ('Christine', 'Kelly', '', [(2024,'$45')]),
    ('John', 'Burke', 'jack.burke@t-mobile.com', [(2024,'$45')]),
    ('Maylin', 'Sinclair', 'maylin.sinclair7@t-mobile.com', [(2024,'$45')]),
    ('Walter', 'Luna de Leon', 'walter.lunadeleon@t-mobile.com', [(2024,'$45')]),
    ('Tetiana', 'Sergiienko', 'tetiana.sergiienko1@t-mobile.com', [(2024,'$45')]),
    ('Maggie', 'Inirio-Akuetey', 'maggie.inirio-akuetey@davispolk.com', [(2024,'$50')]),
    ('Shaniqua', 'Andrews', 'shaniqua.andrews@pfizer.com', [(2024,'$40')]),
    ('Celeste', 'Franco', 'celeste.franco@pfizer.com', [(2024,'$20')]),
    ('Beatriz', 'Vargas', 'beatriz.vargas@pfizer.com', [(2024,'$50')]),
    ('Antonella', 'Giovannetti', 'antonella.giovannetti@pfizer.com', [(2024,'$50')]),
    ('Kate', 'Zolotkovsky', 'katezolotkovsky@gmail.com', [(2024,'$100')]),
    ('Maria Christina', 'Albino', 'albi606@aol.com', [(2024,'$25')]),
    ('Tiffany', 'Yuen', 'tiyuen@microsoft.com', [(2024,'$50')]),
    ('Cynthia', 'Gresham', 'cynthia.gresham.cg@gmail.com', [(2024,'$25')]),
    ('Odalys', 'Ramos', 'odalys.ramos4@t-mobile.com', [(2024,'$50')]),
    ('Walter', 'Luna de Leon', 'walter.lunadeleon@t-mobile.com', [(2024,'$50')]),
    ('Arlene', 'Williams', 'arlene.williams@optum.com', [(2024,'$25')]),
    ('Fernando', 'Bohorquez', 'fbohorquez@bakerlaw.com', [(2024,'$100')]),
    ('Paulina', 'Linares', '', [(2024,'$20')]),
    ('Mayela', 'Calderon', '', [(2024,'$20')]),
    ('Marjorie', 'Cariello', 'marjorie.cariello@icloud.com', [(2024,'$50')]),
    ('Kim', 'Alilou', 'kim@canarymarketing.com', [(2023,'$74'),(2022,'$79')]),
    ('Emilie', 'Perez', 'emilie.perez@twosigma.com', [(2023,'$50')]),
    ('Irgelkha', 'Mejia', 'mejia@adobe.com', [(2022,'$76')]),
    ('Eric', 'Gregware', 'eric.gregware@ihsmarkit.com', [(2022,'$50')]),
    ('Nelson', 'Chu', 'libertyny14@gmail.com', [(2022,'$50')]),
    ('Esteban', 'Perez-Hemminger', 'estebanph@google.com', [(2022,'$50')]),
    ('Cynthia', 'Reddrick', 'cynthiareddrick@msn.com', [(2022,'$50')]),
    ('Cindy', 'Levano', 'cindy.levano@gmail.com', [(2022,'$50')]),
    ('Eric', 'Gregware', 'egregware@outlook.com', [(2022,'$26')]),
    ('Tiago', 'Rachelson', 'tiago.rachelson@gmail.com', [(2022,'$25')]),
    # rows 51-75 (ext IDs in sheet are off-by-one; generating from names)
    ('Laura Fabiola', 'Watts Cesena', 'fabiolawatts@google.com', [(2022,'$10')]),
    ('Catalina', 'Castillo del Moral', 'rodelmoral@google.com', [(2022,'$10')]),
    ('Mariela', 'Batista', 'mariela.batista.32@gmail.com', [(2022,'$5')]),
    ('Alexandria', 'Fernandez', 'alexandriafernandez@ups.com', [(2022,'$5')]),
    ('Vanessa', 'Aliaga', 'vanessadaliaga@gmail.com', []),
    ('Trey', 'King', 'sperez618@yahoo.com', []),
    ('Tiago', 'Rachelson', 'tiago.rachelson@gmail.com', []),
    ('Sharday', 'Sanchez', 'sharday@gmail.com', []),
    ('Noelia', 'Morales', 'mnoelia01@gmail.com', []),
    ('Monica', 'Escobedo', 'mnescobedo17@gmail.com', []),
    ('Manar', 'Zeed', 'zmanar54@gmail.com', []),
    ('Lucy', 'Gonzalez', 'lucygonzales1@gmail.com', []),
    ('Leticia', 'Romero', 'gleticia363@gmail.com', []),
    ('Leidy', 'Valdez', 'leimvaldez@gmail.com', []),
    ('Laureen', 'Delance', 'dellau2002@gmail.com', []),
    ('Kaisen', 'Yao', 'yao.kaisen@gmail.com', []),
    ('Jimmy', 'Benito', 'jimmybenito@gmail.com', []),
    ('Francesca', 'Spinelli', 'spinelli.francesca314@gmail.com', []),
    ('Foluke', 'Tuakli', 'foluketuakli@gmail.com', []),
    ('Delilah', 'Pena', 'penade@nychhc.org', []),
    ('Atiya', 'Butler', 'butlerat@nychhc.org', []),
    ('Annie', 'Kessler', 'anniekessler21@gmail.com', []),
    ('Andrea', 'Martinez', 'andreamartinez1992@msn.com', []),
    ('Amoretta', 'Morris', 'sistahspirit@yahoo.com', []),
    ('Adriannah', 'Rodriguez', 'arodriguez1886@sfc.edu', []),
]

TABS = [
    ('board', BOARD),
    ('amigos', AMIGOS),
    ('campaneros', CAMPANEROS),
    ('aliados', ALIADOS),
]

acct_fields = ['Name', 'Account_External_ID__c', 'RecordTypeId', 'Relationship__c']
cont_fields = ['Contact_External_ID__c', 'FirstName', 'LastName', 'Email', 'AccountId']
opp_fields  = ['Opportunity_External_ID__c', 'Name', 'StageName', 'CloseDate', 'Amount', 'AccountId']

acct_path = f'{PROJ}/indiv_accounts.csv'
cont_path = f'{PROJ}/indiv_contacts.csv'
opp_path  = f'{PROJ}/indiv_opps.csv'

acct_count = cont_count = opp_count = 0
seen_ext = {}

with (open(acct_path, 'w', newline='', encoding='utf-8') as af,
      open(cont_path, 'w', newline='', encoding='utf-8') as cf,
      open(opp_path,  'w', newline='', encoding='utf-8') as of_):
    aw = csv.DictWriter(af, fieldnames=acct_fields)
    cw = csv.DictWriter(cf, fieldnames=cont_fields)
    ow = csv.DictWriter(of_, fieldnames=opp_fields)
    aw.writeheader()
    cw.writeheader()
    ow.writeheader()

    for prefix, rows in TABS:
        for first, last, email, donations in rows:
            first = first.strip()
            last = last.strip()
            if not first and not last:
                continue

            ext_id = make_ext_id(prefix, first, last, seen_ext)
            full_name = f"{first} {last}".strip()
            household_name = f"{last} Household" if last else f"{first} Household"

            aw.writerow({
                'Name': household_name,
                'Account_External_ID__c': ext_id,
                'RecordTypeId': RT_HOUSEHOLD,
                'Relationship__c': 'Funder',
            })
            acct_count += 1

            cw.writerow({
                'Contact_External_ID__c': ext_id,
                'FirstName': first,
                'LastName': last if last else first,
                'Email': email,
                'AccountId': ext_id,  # replaced by real ID via lookup step
            })
            cont_count += 1

            for year, amt_raw in donations:
                amt = clean_amount(amt_raw)
                if not amt:
                    continue
                ow.writerow({
                    'Opportunity_External_ID__c': f"{ext_id}_donation_{year}",
                    'Name': f"{full_name} Donation {year}",
                    'StageName': 'Closed Won',
                    'CloseDate': f"{year}-12-31",
                    'Amount': amt,
                    'AccountId': ext_id,  # replaced by real ID via lookup step
                })
                opp_count += 1

print(f"Accounts : {acct_count} → {acct_path}", file=sys.stderr)
print(f"Contacts : {cont_count} → {cont_path}", file=sys.stderr)
print(f"Opps     : {opp_count} → {opp_path}", file=sys.stderr)
print(f"\nNote: AccountId in contacts/opps CSVs contains the ext ID placeholder.", file=sys.stderr)
print(f"Run resolve_account_ids.py before loading contacts and opps.", file=sys.stderr)
