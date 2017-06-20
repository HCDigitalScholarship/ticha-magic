#!/usr/bin/env python3
import argparse
import os
import functools
from lxml import etree

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
def preview(data, *, spellchoice, abbrchoice):
    html = tostring(xslt_magic.xml_to_html(fromstring(data), spellchoice=spellchoice, 
                                                             abbrchoice=abbrchoice))
    return TEMPLATE.format(html)

def fromstring(data):
    return etree.XML(bytes(data, encoding='utf-8'))
def tostring(root):
    return etree.tostring(root, method='xml', encoding='unicode')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert TEI-encoded XML to HTML')
    parser.add_argument('infile', help='file to read XML from')
    parser.add_argument('outfile', nargs='?', help='file to write to')
    parser.add_argument('--spellchoice', choices=['orig', 'reg-spacing', 'reg-spanish'], 
                                         default='orig')
    parser.add_argument('--abbrchoice', choices=['abbr', 'expan'], default='abbr')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--magic', action='store_true', help='use the Python ticha_magic parser')
    group.add_argument('--preprocess', action='store_true',help='apply the XSLT without paginating')
    group.add_argument('--preview', action='store_true', help='generate an HTML preview')
    args = parser.parse_args()
    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = ifsock.read()
    # decide which transform function to use, and what outfile name to generate
    infile_name = os.path.splitext(args.infile)[0]
    kwargs = {'abbrchoice':args.abbrchoice, 'spellchoice':args.spellchoice}
    if args.magic:
        data = ticha_magic.xml_to_html_from_str(data, **kwargs)
        outfile = args.outfile or infile_name + '.html'
    elif args.preprocess:
        data = tostring(xslt_magic.preprocess(fromstring(data), **kwargs))
        outfile = args.outfile or infile_name + '_preprocessed.xml'
    elif args.preview:
        data = preview(data, **kwargs)
        outfile = args.outfile or infile_name + '_preview.html'
    else:
        data = tostring(xslt_magic.xml_to_html(fromstring(data), **kwargs))
        outfile = args.outfile or infile_name + '.html'
    # write everything to file
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
