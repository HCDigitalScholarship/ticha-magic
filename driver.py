#!/usr/bin/env python3
import argparse
import os

from lxml import etree

from ticha_magic import xml_to_html, preprocess
from make_outline import xml_to_outline


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
    parser.add_argument('--mode', choices=['normal', 'preview', 'preprocess', 'outline'],
                                  default='normal')
    parser.add_argument('--spellchoice', choices=['orig', 'reg-spacing', 'reg-spanish'],
                                         default='orig')
    parser.add_argument('--abbrchoice', choices=['abbr', 'expan'], default='abbr')
    parser.add_argument('--textname', choices=['arte', 'levanto'])
    parser.add_argument('--no-flex', action='store_true', help='Disable FLEx insertion')
    args = parser.parse_args()
    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = ifsock.read()
    # Decide which transform function to use.
    infile_name = os.path.splitext(args.infile)[0]
    # Figure out the text name, to decide what stylesheet to use.
    if args.textname is not None:
        textname = args.textname
    elif 'levanto' in infile_name:
        textname = 'levanto'
    elif 'arte' in infile_name:
        textname = 'arte'
    else:
        textname = ''
    kwargs = {'abbrchoice': args.abbrchoice, 'spellchoice': args.spellchoice, 'textname': textname}
    if args.mode == 'preprocess':
        data = tostring(preprocess(fromstring(data), **kwargs))
    elif args.mode == 'outline':
        data = xml_to_outline(data, textname)
    else:
        if not args.no_flex:
            with open(FLEX_PATH, 'r') as ifsock:
                flex_data = ifsock.read()
        else:
            flex_data = None
        data = tostring(xml_to_html(fromstring(data), flex_data=flex_data, **kwargs))
        if args.mode == 'preview':
            data = _preview_template.format(data)
    print(data)
