#!/usr/bin/env python3

import sys
from bs4 import BeautifulSoup
from html2text import HTML2Text

html2text = HTML2Text()
html2text.unicode_snob = True

ignore_tables = HTML2Text()
ignore_tables.ignore_tables = True


def default_text(field: BeautifulSoup, out):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']
        print(f"{html2text.handle(value)}\n", file=out)


def default_citation(field: BeautifulSoup, out):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']

        print(f"- {ignore_tables.handle(value)}", file=out)

    print(file=out)


def html_text(field: BeautifulSoup, out):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']
        print(f"{value}\n", file=out)


def default_picklist_many(field: BeautifulSoup, out):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']
        print(f"- {value}", file=out)

    print(file=out)

default_picklist_choice = default_picklist_many
default_picklist_one = default_picklist_many
default_orglist_p = default_picklist_many
default_orglist = default_picklist_many
default_xref = default_picklist_many


def not_implemented(field: BeautifulSoup, out):
    print("NotImplemented\n", file=out)

FIELD_NAMES = {
    "Guideline Title": default_text,
    "Bibliographic Source(s)": default_citation,
    "Guideline Status": default_text,
    "Major Recommendations": default_text,
    "Clinical Algorithm(s)": default_text,
    "Disease/Condition(s)": default_text,
    "Guideline Category": default_picklist_many,
    "Clinical Specialty": default_picklist_many,
    "Intended Users": default_picklist_many,
    "Guideline Objective(s)": default_text,
    "Target Population": default_text,
    "Interventions and Practices Considered": default_text,
    "Major Outcomes Considered": default_text,
    "Methods Used to Collect/Select the Evidence": default_picklist_many,
    "Description of Methods Used to Collect/Select the Evidence": default_text,
    "Number of Source Documents": default_text,
    "Methods Used to Assess the Quality and Strength of the Evidence": default_picklist_choice,
    "Rating Scheme for the Strength of the Evidence": html_text,
    "Methods Used to Analyze the Evidence": default_picklist_many,
    "Description of the Methods Used to Analyze the Evidence": default_text,
    "Methods Used to Formulate the Recommendations": default_picklist_choice,
    "Description of Methods Used to Formulate the Recommendations": default_text,
    "Rating Scheme for the Strength of the Recommendations": default_text,
    "Cost Analysis": default_text,
    "Method of Guideline Validation": default_picklist_choice,
    "Description of Method of Guideline Validation": default_text,
    "References Supporting the Recommendations": default_citation,
    "Type of Evidence Supporting the Recommendations": default_text,
    "Potential Benefits": default_text,
    "Potential Harms": default_text,
    "Contraindications": default_text,
    "Qualifying Statements": default_text,
    "Description of Implementation Strategy": default_text,
    "Implementation Tools": default_picklist_many,
    "IOM Care Need": default_picklist_many,
    "IOM Domain": default_picklist_many,
    "Adaptation": default_text,
    "Date Released": default_text,  # TODO: Custom converter
    "Guideline Developer(s)": default_orglist_p,
    "Source(s) of Funding": default_text,
    "Guideline Committee": default_text,
    "Composition of Group That Authored the Guideline": default_text,
    "Financial Disclosures/Conflicts of Interest": default_text,
    "Guideline Endorser(s)": default_orglist,
    "Guideline Availability": default_text,
    "Availability of Companion Documents": default_text,
    "Patient Resources": default_text,
    "NGC Status": default_text,
    "Copyright Statement": default_text,
    "NGC Disclaimer": default_text,
    "Other Disease/Condition(s) Addressed": default_text,
    "FDA Warning/Regulatory Alert": default_text,
    "Guideline Developer Comment": default_text,

    "Disclosure of Guideline Funding Source": default_picklist_one,
    "External Review": default_picklist_one,
    "Updating": default_picklist_one,
    "Specific and Unambiguous Articulation of Recommendations": default_picklist_one,
    "Disclosure and Management of Financial Conflict of Interests": default_picklist_one,
    "Related NQMC Measures": default_xref,
    "Guideline Development Group Composition: Multidisciplinary Group": default_picklist_one,
    "Guideline Development Group Composition: Methodologist Involvement": default_picklist_one,
    "Guideline Development Group Composition: Patient and Public Perspectives": default_picklist_one,
    "Use of a Systematic Review of Evidence: Search Strategy": default_picklist_one,
    "Use of a Systematic Review of Evidence: Study Selection": default_picklist_one,
    "Use of a Systematic Review of Evidence: Synthesis of Evidence": default_picklist_one,
    "Evidence Foundations for and Rating Strength of Recommendations: Grading the Quality or Strength of Evidence": default_picklist_one,
    "Evidence Foundations for and Rating Strength of Recommendations: Benefits and Harms of Recommendations": default_picklist_one,
    "Evidence Foundations for and Rating Strength of Recommendations: Evidence Summary Supporting Recommendations": default_picklist_one,
    "Evidence Foundations for and Rating Strength of Recommendations: Rating the Strength of Recommendations": default_picklist_one,
}


def default_section(section: BeautifulSoup, out):
    print(f"# {section['Name']}\n", file=out)
    for field in section.find_all("Field"):
        print(f"## {field['Name']}\n", file=out)
        FIELD_NAMES.get(field["Name"], not_implemented)(field, out)

SECTION_NAMES = {
    "Benefits/Harms of Implementing the Guideline Recommendations": default_section,
    "General": default_section,
    "Contraindications": default_section,
    "Disclaimer": default_section,
    "Evidence Supporting the Recommendations": default_section,
    "Identifying Information and Availability": default_section,
    "Implementation of the Guideline": default_section,
    "Institute of Medicine (IOM) National Healthcare Quality Report Categories": default_section,
    "Methodology": default_section,
    "NEATS Assessment": default_section,
    "Qualifying Statements": default_section,
    "Recommendations": default_section,
    "Regulatory Alert": default_section,
    "Scope": default_section,
}

# TODO: Tighten up the NEATS Assessment


def main():
    with open(sys.argv[1], "r") as input:
        out = open(sys.argv[2], "w") if (len(sys.argv) >= 3) else sys.stdout
        xml = BeautifulSoup(input.read(), "lxml-xml")
        for section in xml.find_all("Section"):
            # For each section in the guideline...
            SECTION_NAMES.get(section['Name'], default_section)(section, out)


if __name__ == "__main__":
    main()
