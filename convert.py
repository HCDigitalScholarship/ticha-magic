#!/usr/bin/env python3
import argparse
import os
from lxml import etree

import ticha_outline
import ticha_magic
import xslt_magic

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
    <link rel="stylesheet" href="https://ticha.haverford.edu/static/zapotexts/css/page_detail_style.css"/>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"/>
    <script type="text/javascript" src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
  </head>
  <body>
    <div class="container">
      <div class="row text-center">
        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
        </div>
        <div class="col-lg-6 col-md-6 col-sm-6 col-xs-12">
          {}
        </div>
      </div>
    </div>
  </body>
</html>
"""
def preview(data):
    html = xslt_magic.xml_to_html_from_str(data)
    return TEMPLATE.format(html)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='XML to HTML utilities')
    parser.add_argument('infile', help='file to read XML from')
    parser.add_argument('outfile', nargs='?', default='', help='file to write to')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--magic', action='store_true', help='use the Python ticha_magic parser')
    group.add_argument('--preprocess', action='store_true',help='apply the XSLT without paginating')
    group.add_argument('--preview', action='store_true', help='generate an HTML preview')
    group.add_argument('--outline', action='store_true', help='generate an HTML outline')
    args = parser.parse_args()
    infile_name = os.path.splitext(args.infile)[0]
    if args.magic:
        transform_f = ticha_magic.xml_to_html_from_str
        outfile = args.outfile or infile_name + '.html'
    elif args.preprocess:
        transform_f = xslt_magic.preprocess_from_str
        outfile = args.outfile or infile_name + '_preprocessed.xml'
    elif args.preview:
        transform_f = preview
        outfile = args.outfile or infile_name + '_preview.html'
    elif args.outline:
        transform_f = ticha_outline.xml_to_outline
        outfile = args.outfile or infile_name + '_outline.html'
    else:
        transform_f = xslt_magic.xml_to_html_from_str
        outfile = args.outfile or infile_name + '.html'
    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = transform_f(ifsock.read())
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
