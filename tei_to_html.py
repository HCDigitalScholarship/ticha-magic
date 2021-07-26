#!/usr/bin/env python3
import argparse
from lxml import etree
import logging
import os

from src import SPELLCHOICE_ORIG, SPELLCHOICE_SPANISH, ABBRCHOICE_ABBR, TEXT_PARAMS
from src import TEXT_PREVIEW_TEMPLATE, OUTLINE_PREVIEW_TEMPLATE
from src import parse_xml_file, generate_html, generate_outline

def make_all_files(path, text, xslt_path, flex_path):
    files_to_generate = [
      # (suffix,         preview?,  regularized?)
        ('orig',         False,     False),
        ('reg',          False,     True),
        ('orig_preview', True,      False),
        ('reg_preview',  True,      True)
    ]

    for suffix, preview, regularized in files_to_generate:
        tei_root = parse_xml_file(path)
        html_root = generate_html(
            tei_root,
            xslt_path=xslt_path,
            flex_path=flex_path,
            text=text,
            spellchoice=SPELLCHOICE_SPANISH if regularized else SPELLCHOICE_ORIG,
            abbrchoice=ABBRCHOICE_ABBR,
        )

        htmlstr = etree.tostring(html_root, method="xml", encoding="unicode")
        if preview:
            htmlstr = TEXT_PREVIEW_TEMPLATE.format(htmlstr)

        output_path = f'previews/{suffix}.html' if preview else f'{text}_{suffix}.html'
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(htmlstr)

    # Generate outline and preview outline
    for preview in [False, True]:
        output_path = f'previews/outline_preview.html' if preview else f'{text}_outline.html'
        generate_outline(path, output_path, text=text, preview=preview)


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
