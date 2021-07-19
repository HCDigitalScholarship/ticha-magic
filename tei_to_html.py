#!/usr/bin/env python3
import argparse
from lxml import etree
import logging

from src import SPELLCHOICE_ORIG, SPELLCHOICE_SPANISH, ABBRCHOICE_ABBR, PREVIEW_TEMPLATE, TEXT_PARAMS
from src import parse_xml_file, generate_html, generate_outline


def make_all_files(path, text, xslt_path, flex_path):
    files_to_generate = [
      # (suffix,         preview?,  regularized?)
        ('',             False,     False),
        ('_reg',         False,     True),
        ('_preview',     True,      False),
        ('_reg_preview', True,      True)
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
            htmlstr = PREVIEW_TEMPLATE.format(htmlstr)

        output_filename = text + suffix + '.html'
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(htmlstr)

    generate_outline(path, text + "_outline.html", text=text)


parser = argparse.ArgumentParser(description="Convert a TEI-encoded text to HTML.")
parser.add_argument("infile", help="path to a TEI file to convert")
parser.add_argument(
    "-t",
    "-text",
    required=True,
    choices=list(TEXT_PARAMS.keys()),
    help="which text's formatting to use when converting"
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

    logging.debug("Started!")

    if args.t in TEXT_PARAMS:
        xslt_path = TEXT_PARAMS[args.t]["xslt_path"]
        flex_path = TEXT_PARAMS[args.t]["flex_path"]
    else:
        raise RuntimeError("unknown text name: " + args.t)

    make_all_files(args.infile, args.t, xslt_path, flex_path)

    logging.debug("Finished!")
