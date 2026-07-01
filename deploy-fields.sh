#!/bin/bash
mkdir -p force-app/main/default/objects/Contact

# MailChimp_Status__c
cat > force-app/main/default/objects/Contact/MailChimp_Status__c.field-meta.xml << 'FIELD1'
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>MailChimp_Status__c</fullName>
    <externalId>false</externalId>
    <label>MailChimp Status</label>
    <length>100</length>
    <required>false</required>
    <type>Text</type>
</CustomField>
FIELD1

# Note__c
cat > force-app/main/default/objects/Contact/Note__c.field-meta.xml << 'FIELD2'
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Note__c</fullName>
    <externalId>false</externalId>
    <label>Note</label>
    <required>false</required>
    <type>LongTextArea</type>
    <visibleLines>5</visibleLines>
</CustomField>
FIELD2

# Donor_MailChimp__c
cat > force-app/main/default/objects/Contact/Donor_MailChimp__c.field-meta.xml << 'FIELD3'
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Donor_MailChimp__c</fullName>
    <externalId>false</externalId>
    <label>Donor MailChimp Status</label>
    <length>100</length>
    <required>false</required>
    <type>Text</type>
</CustomField>
FIELD3

# Donor_Note__c
cat > force-app/main/default/objects/Contact/Donor_Note__c.field-meta.xml << 'FIELD4'
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Donor_Note__c</fullName>
    <externalId>false</externalId>
    <label>Donor Note</label>
    <required>false</required>
    <type>LongTextArea</type>
    <visibleLines>5</visibleLines>
</CustomField>
FIELD4

echo "✓ Field XMLs created"
ls -la force-app/main/default/objects/Contact/
