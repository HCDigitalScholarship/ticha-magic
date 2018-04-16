#!/usr/bin/env python3
"""Convert TEI-encoded XML into human-readable HTML.

The conversion process goes through the following steps:

    XML -> pseudo-HTML
      XML becomes pseudo-HTML (mostly HTML, but with the TEI <pb/> tags because it is too
      hard to turn these into <div>...</div> using XSLT).

    pseudo-HTML -> HTML
      Pseudo-HTML becomes real HTML, by fixing the <pb/> tags.

    HTML -> HTML with FLEx (optional)
      FLEx insertions from a separate XML file are inserted into the HTML.

Use `convert_tei_file` or `convert_tei_data` to carry out the entire conversion in one fell swoop.
You can also invoke the intermediate functions `convert_tei_to_html`, `paginate`, and `flexify`, but
note that for the sake of efficiency these only take XML/HTML trees as arguments, not strings or
files.
"""
import argparse
import os

from lxml import etree, sax

from xml_to_html import convert_tei_to_html, paginate
from flexify2 import flexify
from common import get_xslt_file, get_output_file


def convert_tei_file(xml_file, out_file, xslt_file, *, flex_file='', with_css=False):
    """Read a TEI-encoded XML document, convert it to HTML, and write the HTML data to the output
    file.

      xml_file: The path to a TEI-encoded XML document.
      html_file: The path to a file to which the HTML data will be written.
      xslt_file: The path to the XSLT stylesheet to be used in the conversion.
      flex_file: If provided, the path to the FLEx XML export containing annotations to be inserted
                 into the HTML.
      with_css: If true, then the output file will be a full HTML document with links to the
                stylesheets used on the Ticha website.

    See the module docstring for details on the conversion process.
    """
    with open(xml_file, 'r', encoding='utf-8') as ifsock:
        with open(out_file, 'w', encoding='utf-8') as ofsock:
            html_data = convert_tei_data(ifsock.read(), xslt_file, flex_file=flex_file)
            if with_css:
                print('Adding CSS links and HTML shell')
                html_data = WITH_CSS_TEMPLATE.format(html_data)
            ofsock.write(html_data)


# The HTML template used by convert_tei_file when the with_css keyword argument is true.
WITH_CSS_TEMPLATE = """\
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


def convert_tei_data(xml_data, xslt_file, *, flex_file=''):
    """Convert XML data (as a string) into HTML data (as a string). `xslt_file` and `flex_file` are
    the same as in convert_tei_file.
    """
    xml_root = etree.XML(bytes(xml_data, encoding='utf-8'))
    pseudo_html_root = convert_tei_to_html(xml_root, xslt_file, abbrchoice='abbr', spellchoice='orig')
    html_root = paginate(pseudo_html_root, '')
    if flex_file:
        html_root = flexify(html_root, flex_file)
    return etree.tostring(html_root, method='xml', encoding='unicode')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    parser.add_argument('-o', '--outfile')
    parser.add_argument('-f', '--flex', default='')
    parser.add_argument('-x', '--xslt')
    parser.add_argument('-w', '--with-css', action='store_true')
    args = parser.parse_args()

    # Infer the output path, if not given.
    if args.outfile:
        outfile = args.outfile
    else:
        outfile = get_output_file(args.infile)
        print('Inferred output file', outfile)

    # Infer the XSLT file, if not given.
    if args.xslt:
        xslt_file = args.xslt
    else:
        xslt_file = get_xslt_file(args.infile)
        print('Inferred XSLT file', xslt_file)

    # Run the conversion.
    convert_tei_file(args.infile, outfile, xslt_file, flex_file=args.flex, with_css=args.with_css)
