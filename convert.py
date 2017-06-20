#!/usr/bin/env python3
import argparse
import os
import functools
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
    html = string_adapter(xslt_magic.xml_to_html)(data, spellchoice='orig', abbrchoice='abbr')
    return TEMPLATE.format(html)

def string_adapter(f):
    """Given a function that takes an lxml.Element object as its first argument and returns an
       lxml.Element object, return a function that takes a string as its first argument and returns
       a string.
    """
    def from_string(data):
        return etree.XML(bytes(data, encoding='utf-8'))
    def to_string(root):
        return etree.tostring(root, method='xml', encoding='unicode')
    return lambda data, *args, **kwargs: to_string(f(from_string(data), *args, **kwargs))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='XML to HTML utilities')
    parser.add_argument('infile', help='file to read XML from')
    parser.add_argument('outfile', nargs='?', default='', help='file to write to')
    parser.add_argument('--spellchoice', choices=['orig', 'reg-spacing', 'reg-spanish'], 
                                         default='orig')
    parser.add_argument('--abbrchoice', choices=['abbr', 'expan'], default='abbr')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--magic', action='store_true', help='use the Python ticha_magic parser')
    group.add_argument('--preprocess', action='store_true',help='apply the XSLT without paginating')
    group.add_argument('--preview', action='store_true', help='generate an HTML preview')
    group.add_argument('--outline', action='store_true', help='generate an HTML outline')
    args = parser.parse_args()
    infile_name = os.path.splitext(args.infile)[0]
    # decide which transform function to use, and what outfile name to generate
    if args.magic:
        transform_f = ticha_magic.xml_to_html_from_str
        outfile = args.outfile or infile_name + '.html'
    elif args.preprocess:
        transform_f = string_adapter(xslt_magic.preprocess)
        outfile = args.outfile or infile_name + '_preprocessed.xml'
    elif args.preview:
        transform_f = preview
        outfile = args.outfile or infile_name + '_preview.html'
    elif args.outline:
        transform_f = ticha_outline.xml_to_outline
        outfile = args.outfile or infile_name + '_outline.html'
    else:
        kwargs = {'abbrchoice':args.abbrchoice, 'spellchoice':args.spellchoice}
        transform_f = string_adapter(functools.partial(xslt_magic.xml_to_html, **kwargs))
        outfile = args.outfile or infile_name + '.html'
    # write everything to file
    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = transform_f(ifsock.read())
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
