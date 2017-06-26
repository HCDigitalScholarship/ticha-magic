#!/usr/bin/env python3
"""Convert TEI-encoded XML into human-readable HTML."""
import sys
import os
import io
import argparse
import xml.etree.ElementTree as ET

from lxml import etree, sax


XSLT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'transform.xslt')

class AugmentedElementTreeContentHandler(sax.ElementTreeContentHandler):
    """Augment the lxml implementation to support better error messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.real_tag_stack = []

    def startElementNS(self, ns_name, qname, attributes=None):
        self.real_tag_stack.append(qname)
        super().startElementNS(ns_name, qname, attributes)

    def endElementNS(self, ns_name, qname):
        try:
            super().endElementNS(ns_name, qname)
            self.real_tag_stack.pop()
        except sax.SaxError as e:
            print('Tried to close ' + qname, end='')
            if self.real_tag_stack:
                print(', but last opened tag was ' + self.real_tag_stack[-1])
            else:
                print(', but no tags have been opened')
            raise e


class TEIPager(AugmentedElementTreeContentHandler):
    namespace = 'http://www.w3.org/XML/1998/namespace'
    # used on the tag stack to indicate a dummy element that should not be opened/closed
    dummy_elem = ('', '', None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The tag stack is a stack of (ns_name, qname, attributes) tuples that represent the current
        # path in the tree. Dummy tags (see cls.dummy_elem) may be pushed onto the stack. These
        # should always be ignored.
        self.tag_stack = []
        self.page = 0
        self.line = 1
        self.section = ''

    def startElementNS(self, ns_name, qname, attributes=None):
        if tag_eq(qname, 'pb'):
            if attributes.get((None, 'type')) != 'pdf':
                self.handlePageBreak()
        elif tag_eq(qname, 'cb'):
            n = attributes.get((None, 'n'))
            self.handleColumnBreak(n)
        elif tag_eq(qname, 'body'):
            super().startElementNS((None, 'div'), 'div')
            attrs = {(None, 'class'): 'page', (None, 'n'): str(self.page), 
                     (None, 'section'): self.section}
            super().startElementNS((None, 'div'), 'div', attrs)
        else:
            if tag_eq(qname, 'br'):
                self.line += 1
            if tag_eq(qname, 'div'):
                if attributes:
                    new_section = attributes.get((None, 'id'))
                    if new_section:
                        # make 2.01 into 2.1
                        self.section = new_section.replace('.0', '.')
                        self.tag_stack.append(self.dummy_elem)
                        return
            self.tag_stack.append( (ns_name, qname, attributes) )
            super().startElementNS(ns_name, qname, attributes)

    def handlePageBreak(self):
        self.line = 1
        self.page += 1
        self.closeAllTags()
        super().endElementNS((None, 'div'), 'div')
        attrs = {(None, 'class'): 'page', (None, 'n'): str(self.page), 
                 (None, 'section'): self.section}
        super().startElementNS((None, 'div'), 'div', attrs)
        self.reopenAllTags()

    def handleColumnBreak(self, n):
        if n == '1':
            # value of '1' indicates start of column section
            self.startElementNS((None, 'div'), 'div')
            self.startElementNS((None, 'div'), 'div', {(None, 'class'):'col-xs-6'})
        elif n == '':
            # empty value indicates end of column section
            self.endElementNS((None, 'div'), 'div')
            self.endElementNS((None, 'div'), 'div')
        else:
            self.endElementNS((None, 'div'), 'div')
            self.startElementNS((None, 'div'), 'div', {(None, 'class'):'col-xs-6'})

    def endElementNS(self, ns_name, qname):
        # ignore self-closing <pb> and <cb> tags; they were already handled by startElementNS
        if tag_eq(qname, 'body'):
            super().endElementNS((None, 'div'), 'div')
            super().endElementNS((None, 'div'), 'div')
        elif not tag_eq(qname, 'pb') and not tag_eq(qname, 'cb'):
            closes = self.tag_stack.pop()
            if closes != self.dummy_elem:
                try:
                    super().endElementNS(ns_name, qname)
                except sax.SaxError as e:
                    print('Error on page {0.page}, line {0.line}'.format(self))
                    raise e

    def closeAllTags(self):
        for ns_name, qname, _ in reversed(self.tag_stack):
            if ns_name or qname:
                super().endElementNS(ns_name, qname)

    def reopenAllTags(self):
        for ns_name, qname, attributes in self.tag_stack:
            if ns_name or qname:
                super().startElementNS(ns_name, qname, attributes)


def xml_to_html(xml_root, **kwargs):
    """Convert the TEI-encoded XML document to an HTML document."""
    return paginate(preprocess(xml_root, **kwargs))

def preprocess(root, **kwargs):
    """Apply the XSLT stylesheet to the TEI-encoded XML document, but do not paginate."""
    xslt_transform = etree.XSLT(etree.parse(XSLT_PATH).getroot())
    for key, val in kwargs.items():
        if isinstance(val, str):
            kwargs[key] = etree.XSLT.strparam(val)
    ret = xslt_transform(root, **kwargs)
    error_msg = str(xslt_transform.error_log).strip()
    if error_msg:
        print(error_msg)
    return ret

def paginate(root):
    """Paginate the TEI-encoded XML document. This entails removing all <pb/> elements and adding
       <div class="page">...</div> elements to wrap each page. This function should be called
       after preprocessing.
    """
    # I do not understand why it is necessary to cast to bytes here
    handler = TEIPager()
    sax.saxify(root, handler)
    return handler.etree


def tag_eq(tag_in_document, tag_to_check):
    """Compare equality of tags ignoring namespaces. Note that this is not commutative."""
    return tag_in_document == tag_to_check or tag_in_document.endswith(':' + tag_to_check)


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
    if args.preprocess:
        data = tostring(preprocess(fromstring(data), **kwargs))
        outfile = args.outfile or infile_name + '_preprocessed.xml'
    else:
        data = tostring(xml_to_html(fromstring(data), **kwargs))
        outfile = args.outfile or infile_name + '.html'
    if args.preview:
        data = _preview_template.format(data)
    # write everything to file
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
