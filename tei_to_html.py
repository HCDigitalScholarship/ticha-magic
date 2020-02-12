#!/usr/bin/env python3
import argparse
from lxml import etree

from src import SPELLCHOICE_ORIG, ABBRCHOICE_ABBR, PREVIEW_TEMPLATE, TEXT_PARAMS
from src import parse_xml_file, generate_html, generate_outline


def make_all_files(path, text, xslt_path, flex_path):
    files_to_generate = [
        ('', False),
        ('_reg', False),
        ('_preview', True),
        ('_reg_preview', True)
    ]

    for suffix, preview in files_to_generate:
        tei_root = parse_xml_file(path)
        html_root = generate_html(
            tei_root,
            xslt_path=xslt_path,
            flex_path=flex_path,
            text=text,
            spellchoice=SPELLCHOICE_ORIG,
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
parser.add_argument("infile", help="Path to TEI file to convert")
parser.add_argument(
    "-t",
    required=True,
    choices=list(TEXT_PARAMS.keys()),
)


if __name__ == "__main__":
    args = parser.parse_args()

    if args.t in TEXT_PARAMS:
        xslt_path = TEXT_PARAMS[args.t]["xslt_path"]
        flex_path = TEXT_PARAMS[args.t]["flex_path"]
    else:
        raise RuntimeError("unknown text name: " + args.t)

    make_all_files(args.infile, args.t, xslt_path, flex_path)
