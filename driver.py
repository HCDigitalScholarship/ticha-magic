#!/usr/bin/env python3
import argparse
import os
import logging
import sys

from lxml import etree

from ticha_magic import xml_to_html, preprocess, logger


FLEX_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'flex.xml')


_preview_template = """\
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
      <div class="row text-left">
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

def fromstring(data):
    return etree.XML(bytes(data, encoding='utf-8'))
def tostring(root):
    return etree.tostring(root, method='xml', encoding='unicode')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert TEI-encoded XML to HTML')
    parser.add_argument('infile', help='file to read XML from')
    parser.add_argument('outfile', nargs='?', help='file to write to')
    parser.add_argument('--preview', action='store_true', help='generate an HTML preview')
    parser.add_argument('--preprocess', action='store_true', help='apply the XSLT without paginating')
    parser.add_argument('--spellchoice', choices=['orig', 'reg-spacing', 'reg-spanish'], 
                                         default='orig')
    parser.add_argument('--abbrchoice', choices=['abbr', 'expan'], default='abbr')
    args = parser.parse_args()
    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = ifsock.read()
    # decide which transform function to use, and what outfile name to generate
    infile_name = os.path.splitext(args.infile)[0]
    kwargs = {'abbrchoice':args.abbrchoice, 'spellchoice':args.spellchoice, 'textname':infile_name}
    # configure the logger to print messages to stderr (as well as to the Django logs)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    if args.preprocess:
        data = tostring(preprocess(fromstring(data), **kwargs))
        outfile = args.outfile or infile_name + '_preprocessed.xml'
    else:
        with open(FLEX_PATH, 'r') as ifsock:
            flex_data = ifsock.read()
        data = tostring(xml_to_html(fromstring(data), flex_data=flex_data, **kwargs))
        outfile = args.outfile or infile_name + '.html'
    if args.preview:
        data = _preview_template.format(data)
    # write everything to file
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
