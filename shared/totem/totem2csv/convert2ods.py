from pathlib import Path

from lxml import etree
from odf.table import TableRow, TableCell
from odf.text import P


def create_sheet_doc():
    from odf.opendocument import OpenDocumentSpreadsheet
    return OpenDocumentSpreadsheet()


def create_sheet_table(sheet_doc, sheet_name):
    from odf.table import Table
    sheet = sheet_doc.spreadsheet
    return Table(parent=sheet, name=sheet_name)


def save_sheet_doc(sheet_doc, file_prefix: str):
    sheet_doc.save('%s.ods' % file_prefix)


def export_xml_tab_to_sheet(xml_file: Path, sheet, sheet_name):

    table = create_sheet_table(sheet, sheet_name)

    TAGS = ['csv', 'header', 'column', 'data', 'row', 'cell']

    with xml_file.open('rb') as fdin:

        column_list = []
        row_data = {}
        for evt, elt in etree.iterparse(fdin, tag=TAGS, events=("start", "end")):
            if evt == 'end' and elt.tag == 'column':
                column_list.append(elt.attrib['name'])
                continue
            if evt == 'end' and elt.tag == 'header':
                tr = TableRow(parent=table)
                for col_name in column_list:
                    tc = TableCell(parent=tr)
                    p = P(parent=tc, text=col_name) # / stylename=tablecontents
                continue
            if elt.tag == 'row':
                if evt == 'start':
                    row_data = {}
                else:
                    tr = TableRow(parent=table)
                    for col_name in column_list:
                        tc = TableCell(parent=tr)
                        p = P(parent=tc, text=row_data.get(col_name,""))  # / stylename=tablecontents
                continue
            if elt.tag == 'cell' and evt == 'start':
                row_data[elt.attrib['name']] = elt.attrib['value']

