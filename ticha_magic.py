#!/usr/bin/env python3
"""Convert TEI-encoded XML into human-readable HTML."""
import sys
import os
import io
import argparse

from lxml import etree, sax

from . import flex


XSLT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'transform.xslt')
FLEX_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'flex.xml')


class AugmentedContentHandler(sax.ElementTreeContentHandler):
    """Augment the lxml implementation to support better error messages and provide the useful
       (though namespace-unaware) startElement and endElement methods.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.real_tag_stack = []

    def startElement(self, name, attributes=None):
        if attributes is not None:
            attributes = {(None, key): val for key, val in attributes.items()}
        AugmentedContentHandler.startElementNS(self, (None, name), name, attributes)

    def endElement(self, name):
        AugmentedContentHandler.endElementNS(self, (None, name), name)

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


class TEIPager(AugmentedContentHandler):
    """A SAX parser that transforms <pb/> and <cb/> tags into <div>s that wrap pages and columns,
       respectively.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The tag stack is a stack of (ns_name, qname, attributes) tuples that represent the current
        # path in the tree.
        self.tag_stack = []
        self.page = 0
        self.line = 1

    def startElementNS(self, ns_name, qname, attributes=None):
        if tag_eq(qname, 'pb'):
            if attributes.get((None, 'type')) != 'pdf':
                recto_verso_no = attributes.get((None, 'n'), '')
                self.handlePageBreak(recto_verso_no)
        elif tag_eq(qname, 'cb'):
            n = attributes.get((None, 'n'))
            self.handleColumnBreak(n)
        elif tag_eq(qname, 'body'):
            self.startElement('div')
            self.startNewPageDiv(str(self.page), '0')
        else:
            if tag_eq(qname, 'br'):
                self.line += 1
            self.tag_stack.append( (ns_name, qname, attributes) )
            super().startElementNS(ns_name, qname, attributes)

    def handlePageBreak(self, recto_verso_no):
        self.line = 1
        self.page += 1
        self.closeAllTags()
        self.endElement('div')
        self.startNewPageDiv(str(self.page), recto_verso_no)
        self.reopenAllTags()

    def startNewPageDiv(self, page_no, recto_verso_no):
        self.startElement('div', {'class': 'page', 'data-n': page_no, 'data-rvn': recto_verso_no})

    def handleColumnBreak(self, n):
        if n == '1':
            # value of '1' indicates start of column section
            self.startElement('div')
            self.startElement('div', {'class': 'col-xs-6'})
        elif n == '':
            # empty value indicates end of column section
            self.endElement('div')
            self.endElement('div')
        else:
            self.endElement('div')
            self.startElement('div', {'class': 'col-xs-6'})

    def endElementNS(self, ns_name, qname):
        # ignore self-closing <pb> and <cb> tags; they were already handled by startElementNS
        if tag_eq(qname, 'body'):
            self.endElement('div')
            self.endElement('div')
        elif not tag_eq(qname, 'pb') and not tag_eq(qname, 'cb'):
            closes = self.tag_stack.pop()
            try:
                super().endElementNS(ns_name, qname)
            except sax.SaxError as e:
                print('Error on page {0.page}, line {0.line}'.format(self))
                raise e

    def closeAllTags(self):
        for ns_name, qname, _ in reversed(self.tag_stack):
            super().endElementNS(ns_name, qname)

    def reopenAllTags(self):
        for ns_name, qname, attributes in self.tag_stack:
            super().startElementNS(ns_name, qname, attributes)


def xml_to_html(xml_root, flex_data=None, **kwargs):
    """Convert the TEI-encoded XML document to an HTML document."""
    paginated_tree = paginate(preprocess(xml_root, **kwargs))
    if flex_data:
        flex_dict = flex.FLExDict(flex_data)
        return flex.flexify(paginated_tree, flex_dict)
    else:
        return paginated_tree

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
        with open(FLEX_PATH, 'r') as ifsock:
            flex_data = ifsock.read()
        data = tostring(xml_to_html(fromstring(data), flex_data=flex_data, **kwargs))
        outfile = args.outfile or infile_name + '.html'
    if args.preview:
        data = _preview_template.format(data)
    # write everything to file
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
