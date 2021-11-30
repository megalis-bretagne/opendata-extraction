#!/usr/bin/env python3
"""
Transform a XML CSV file into a CSV.
"""
import csv
import sys
from pathlib import Path

from lxml import etree

from convert2ods import create_sheet_doc, save_sheet_doc, export_xml_tab_to_sheet

TEMP_XML_FILE = '/tmp/totem.xml'
TEMP_CSV_FILE = '/tmp/totem.csv'

sheets = [{
    "xsl": "/appli/shared/totem/totem2csv/xsl/totem2xmlcsv.xsl",
    "name": "Bugdet"
}]


def convert_totem(totem_file: str, output_prefix: str):

    #sheetDoc = create_sheet_doc()

    pdc_file = extract_plan_de_compte(totem_file)

    for sheetConf in sheets:
        sheet_name = sheetConf.get("name")
        sheet_xsl = sheetConf.get("xsl")

        #csv_file_name = output_prefix + '.%s.csv' % sheet_name
        print("Extracting sheet %s to file %s" % (sheet_name, TEMP_CSV_FILE))

        extract_xml_table(totem_file, pdc_file, sheet_xsl, TEMP_XML_FILE)

        csv_file = Path(TEMP_CSV_FILE)

        #export_xml_tab_to_sheet(Path(TEMP_XML_FILE), sheetDoc, sheet_name)
        convert_xml_tab_to_csv(Path(TEMP_XML_FILE), csv_file)

    #save_sheet_doc(sheetDoc, output_prefix)


def extract_plan_de_compte(totem_file):

    namespaces = {'db': 'http://www.minefi.gouv.fr/cp/demat/docbudgetaire'}  # add more as needed

    tree = etree.parse(totem_file)
    nomenclature: str = tree.findall('/db:Budget/db:EnTeteBudget/db:Nomenclature', namespaces)[0].attrib.get('V')
    year = tree.findall('/db:Budget/db:BlocBudget/db:Exer', namespaces)[0].attrib.get('V')
    print("Version de plan de compte trouvée: (%s, %s)" % (year, nomenclature))

    (n1, n2) = nomenclature.split('-', 1)
    return "../norme-budgetaire-downloader/output/%s/%s/%s/planDeCompte.xml" % (year, n1, n2)


def extract_xml_table(totem_file, pdc_file, xsl_file, temp_file):

    bash_command = "xmlstarlet tr %s -s plandecompte=%s %s | xmlstarlet fo - > " \
                  "%s " % (xsl_file, pdc_file, totem_file, temp_file)
    import subprocess
    process = subprocess.Popen(["bash", "-c", bash_command], stdout=subprocess.PIPE)
    output, error = process.communicate()

    if error is not None:
        raise error


def convert_xml_tab_to_csv(xml_file: Path, csv_file: Path):

    TAGS = ['csv', 'column', 'data', 'row', 'cell']

    with xml_file.open('rb') as fdin:
        with csv_file.open('wt', encoding="UTF-8") as fdout:

            writer = csv.writer(fdout)
            column_list = []
            row_data = {}
            for evt, elt in etree.iterparse(fdin, tag=TAGS, events=("start", "end")):
                if evt == 'end' and elt.tag == 'column':
                    column_list.append(elt.attrib['name'])
                    continue
                if evt == 'end' and elt.tag == 'header':
                    writer.writerow(column_list)
                    continue
                if elt.tag == 'row':
                    if evt == 'start':
                        row_data = {}
                    else:
                        writer.writerow([row_data.get(col_name,"") for col_name in column_list])
                    continue
                if elt.tag == 'cell' and evt == 'start':
                    row_data[elt.attrib['name']] = elt.attrib['value']


def main():
    if len(sys.argv) != 3:
        sys.stderr.write(f"usage: {sys.argv[0]} <totem_file> <output_prefix>\n")
        sys.exit(1)

    totem_file = sys.argv[1]
    totem_file_path = Path(sys.argv[1])
    if not totem_file_path.exists():
        sys.stderr.write(f"input file {totem_file} not found.")
        sys.exit(1)

    output_prefix = sys.argv[2]

    convert_totem(totem_file, output_prefix)


if __name__ == '__main__':
    sys.exit(main())
