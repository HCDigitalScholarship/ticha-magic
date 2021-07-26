#!/usr/bin/env python3
import argparse
from lxml import etree
import logging
import os

from src import SPELLCHOICE_ORIG, SPELLCHOICE_SPANISH, ABBRCHOICE_ABBR, TEXT_PARAMS
from src import TEXT_PREVIEW_TEMPLATE, OUTLINE_PREVIEW_TEMPLATE
from src import parse_xml_file, generate_html, generate_outline

def make_all_files(path, text, xslt_path, flex_path):
    versions_to_generate = [
      # (suffix, regularized?)
        ('orig', False),
        ('reg',  True)
    ]

    tei_root = parse_xml_file(path)

    # Generate HTML for each option from the XML
    for suffix, regularized in versions_to_generate:
        html_root = generate_html(
            tei_root,
            xslt_path=xslt_path,
            flex_path=flex_path,
            text=text,
            spellchoice=SPELLCHOICE_SPANISH if regularized else SPELLCHOICE_ORIG,
            abbrchoice=ABBRCHOICE_ABBR,
        )

        # Write output
        htmlstr = etree.tostring(html_root, method="xml", encoding="unicode")
        with open(f'{text}_{suffix}.html', "w", encoding="utf-8") as f:
            f.write(htmlstr)

        # Write preview
        preview_htmlstr = TEXT_PREVIEW_TEMPLATE.format(htmlstr)
        with open(f'previews/{suffix}.html', "w", encoding="utf-8") as f:
            f.write(preview_htmlstr)

    # Generate outline
    generate_outline(path, f'{text}_outline.html', text=text, preview=False)

    # Generate preview outline
    generate_outline(path, 'previews/outline_preview.html', text=text, preview=True)


parser = argparse.ArgumentParser(description="Convert a TEI-encoded text to HTML.")
parser.add_argument("infile", help="path to a TEI file to convert")
parser.add_argument(
    "-t",
    "--text",
    required=True,
    choices=list(TEXT_PARAMS.keys()),
    help="text ID indicating what formatting to use when converting"
)
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    default=False,
    help="print debugging output"

)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.info(f'Starting! converting TEI in {args.infile} to Ticha HTML')

    if args.text in TEXT_PARAMS:
        xslt_path = TEXT_PARAMS[args.text]["xslt_path"]
        flex_path = TEXT_PARAMS[args.text]["flex_path"]
    else:
        raise RuntimeError("unknown text name: " + args.text)

    make_all_files(args.infile, args.text, xslt_path, flex_path)

    logging.info(f'Finished! Wrote 3 files to {os.getcwd()} and 3 preview files to {os.getcwd()}/preview')
