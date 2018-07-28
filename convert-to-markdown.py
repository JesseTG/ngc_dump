#!/usr/bin/env python3

import argparse
from io import IOBase
import re
import sys


from bs4 import BeautifulSoup
from html2text import HTML2Text

html2text = HTML2Text()
html2text.unicode_snob = True
html2text.bypass_tables = True
html2text.body_width = 0

ignore_tables = HTML2Text()
ignore_tables.unicode_snob = True
ignore_tables.ignore_tables = True
ignore_tables.single_line_break = True
ignore_tables.body_width = 0

RADIOACTIVE_SYMBOL_OLD = "http://guideline.gov/images/image_radioactive.gif"
# This one was taken offline because it was hosted on the NGC
RADIOACTIVE_SYMBOL_NEW = "https://assets-cdn.github.com/images/icons/emoji/unicode/2622.png"


def default_text(field: BeautifulSoup, out: IOBase):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']
        print(f"{html2text.handle(value)}", file=out)


def default_citation(field: BeautifulSoup, out: IOBase):
    for field_value in field.find_all('FieldValue'):
        html = field_value['Value']
        html = BeautifulSoup(html, "lxml")
        td = html.find("td")

        print(f"- {ignore_tables.handle(td.prettify()).strip()}", file=out)

    print(file=out)


def html_text(field: BeautifulSoup, out: IOBase):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']
        print(f"{value}\n", file=out)


def default_picklist_many(field: BeautifulSoup, out: IOBase):
    for field_value in field.find_all('FieldValue'):
        value = field_value['Value']
        print(f"- {value}", file=out)

    print(file=out)

default_picklist_choice = default_picklist_many
default_picklist_one = default_picklist_many
default_orglist_p = default_picklist_many
default_orglist = default_picklist_many
default_xref = default_picklist_many


def not_implemented(field: BeautifulSoup, out: IOBase):
    print("NotImplemented\n", file=out)

# TODO: Link internally with the case-insensitive regex "see the .*\"(.+)\" field"
# TODO: Substitute math and units (cm, pi r2, >>>)


def should_be_h3(element: BeautifulSoup) -> bool:
    # Returns true if the element is of either form:
    # <p><strong><span style="text-decoration: underline;">text</span></strong></p>
    # <p><span style="text-decoration: underline;"><strong>text</strong></span></p>

    if element.name != 'p':
        return False

    if any(e.name == 'table' for e in element.parents):
        return False

    strong = element.find_all("strong")
    span = element.find_all("span", style="text-decoration: underline;")

    if len(span) != 1 or len(strong) != 1:
        return False

    return span[0].parent == strong[0] or strong[0].parent == span[0]


def should_be_h4(element: BeautifulSoup) -> bool:
    # Returns true if the element is of the form:
    # <p><strong>text</strong></p>

    if element.name != 'p':
        return False

    if any(e.name == 'table' for e in element.parents):
        return False

    strong = element.find_all("strong")
    if len(strong) != 1:
        return False

    if strong[0].text != element.text:
        # If the <strong> is a bold segment in the <p> but is not the entire <p>...
        return False

    return True


def should_be_h5(element: BeautifulSoup) -> bool:
    # Returns true if the element is of the form:
    # <p><em>text</em></p>

    if element.name != 'p':
        return False

    if any(e.name == 'table' for e in element.parents):
        return False

    em = element.find_all("em")
    if len(em) != 1:
        return False

    return True


def should_be_h6(element: BeautifulSoup) -> bool:
    # Returns true if the element is of the form:
    # <p><span style="text-decoration: underline;">text</span></p>

    if element.name != 'p':
        return False

    if any(e.name == 'table' for e in element.parents):
        return False

    span = element.find_all("span", style="text-decoration: underline;")
    if len(span) != 1:
        return False

    strong = element.find_all("strong")
    # To disambiguate from h4 candidates

    if len(strong) != 0:
        return False

    return True


def major_recommendations(field: BeautifulSoup, out: IOBase):
    # TODO: Condence ( spaces inside parens ) to be (sane)

    html = field.find('FieldValue')['Value']
    html = BeautifulSoup(html, "lxml")

    for h3 in html.find_all(should_be_h3):
        h3.name = "h3"
        h3.string = h3.text

    for h4 in html.find_all(should_be_h4):
        h4.name = "h4"
        h4.string = h4.text

    for h5 in html.find_all(should_be_h5):
        h5.name = "h5"
        h5.string = h5.text

    for h6 in html.find_all(should_be_h6):
        h6.name = "h6"
        h6.string = h6.text

    for img in html.find_all("img", src=RADIOACTIVE_SYMBOL_OLD):
        # For each use of the radioactive symbol...
        # (The <img>'s referred to an icon on guideline.gov, which no longer exists)
        img["src"] = RADIOACTIVE_SYMBOL_NEW
        img["width"] = 20
        img["height"] = 20

    # The tables have complicated layouts: they use different row and column spans a lot.
    # I iterate over the HTML elements because if I pass the whole thing into
    # html2text.prettify(), the table will get fucked up.
    children = (html.find("div") or html.find("body")).children

    for i in children:
        if i.name is not None:
            # If this is a non-text element...
            if i.name == 'table':
                # If this is a table element...
                print(i.prettify(), file=out, end="")
                # Just print it out
            else:
                print(html2text.handle(i.prettify()), file=out, end="")
                # Convert it to Markdown

FIELD_NAMES = {
    "Guideline Title": default_text,
    "Bibliographic Source(s)": default_citation,
    "Guideline Status": default_text,
    "Major Recommendations": major_recommendations,
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


def default_section(section: BeautifulSoup, out: IOBase):
    print(f"# {section['Name']}\n", file=out)
    for field in section.find_all("Field"):
        print(f"## {field['Name']}\n", file=out)
        FIELD_NAMES.get(field["Name"], not_implemented)(field, out)


QUOTE = r'"'
ESCAPE_QUOTE = r'\"'


def generate_front_matter(xml: BeautifulSoup, out: IOBase):
    print("---", file=out)
    title = xml.find("Field", Name="Guideline Title")
    if title is not None:
        html = title.find("FieldValue")["Value"]
        html = BeautifulSoup(html, "lxml")
        print(f'title: "{html.text.replace(QUOTE, ESCAPE_QUOTE)}"', file=out)

    match = re.search(r"ngc-(\d+)\.xml", args.input.name)
    if match is not None:
        # If the file is named ngc-{some numbers}.xml...
        print(f'id: {match[1]}', file=out)
        print(f'permalink: /:collection/{match[1]}', file=out)

    print("---\n", file=out)

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

parser = argparse.ArgumentParser(
    description='Convert the NGC XMLs to Markdown'
)

parser.add_argument(
    "--front-matter",
    help="Generate YAML front matter for Jekyll",
    action="store_true"
)

parser.add_argument(
    "input",
    help="Input",
    type=argparse.FileType("r")
)

parser.add_argument(
    "output",
    help="Output (default stdout)",
    type=argparse.FileType("w"),
    default="/dev/stdout",
    nargs="?"
)

args = parser.parse_args()


def main():

    xml = BeautifulSoup(args.input.read(), "lxml-xml")

    if args.front_matter:
        generate_front_matter(xml, args.output)

    for section in xml.find_all("Section"):
        # For each section in the guideline...
        SECTION_NAMES.get(section['Name'], default_section)(
            section, args.output)


if __name__ == "__main__":
    main()
