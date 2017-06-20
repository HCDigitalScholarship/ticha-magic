#!/usr/bin/env python3
"""Convert TEI-encoded XML into human-readable HTML.

This module contains two separate conversion programs: the new one, which uses mostly XSLT with
some Python, and the old one (a descendant of the venerable ticha_magic script) which uses pure
Python. The old one is deprecated and will probably be removed at some point, but we keep it
around in case the new design proves horribly misguided.
"""
import sys
import os
import io
import argparse
import xml.etree.ElementTree as ET

from lxml import etree, sax



### THE CURRENT CONVERSION PROGRAM, USING MOSTLY XSLT ###

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag_stack = []
        self.page = 0
        self.line = 1

    def startElementNS(self, ns_name, qname, attributes=None):
        #print(qname)
        if tag_eq(qname, 'pb'):
            if attributes.get((None, 'type')) != 'pdf':
                self.handlePageBreak()
        elif tag_eq(qname, 'cb'):
            n = attributes.get((None, 'n'))
            self.handleColumnBreak(n)
        elif tag_eq(qname, 'body'):
            super().startElementNS((None, 'div'), 'div')
            super().startElementNS((None, 'div'), 'div', {(None, 'class'):'page',
                                                          (None, 'n'):str(self.page),})
        else:
            if tag_eq(qname, 'br'):
                self.line += 1
            self.tag_stack.append( (ns_name, qname, attributes) )
            super().startElementNS(ns_name, qname, attributes)

    def handlePageBreak(self):
        self.line = 1
        self.page += 1
        self.closeAllTags()
        super().endElementNS((None, 'div'), 'div')
        super().startElementNS((None, 'div'), 'div', {(None, 'class'):'page',
                                                      (None, 'n'):str(self.page),})
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
            self.tag_stack.pop()
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


def xml_to_html(xml_root, **kwargs):
    """Convert the TEI-encoded XML document to an HTML document."""
    return paginate(preprocess(xml_root, **kwargs))

def preprocess(root, **kwargs):
    """Apply the XSLT stylesheet to the TEI-encoded XML document, but do not paginate."""
    xslt_transform = etree.XSLT(etree.parse(XSLT_PATH).getroot())
    for key, val in kwargs.items():
        if isinstance(val, str):
            kwargs[key] = etree.XSLT.strparam(val)
    return xslt_transform(root, **kwargs)

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



## THE OLD CONVERSION PROGRAM, IN PURE PYTHON ##

HEADER_TAGS = ('TEI', 'teiHeader', 'fileDesc', 'titleStmt', 'title',
    'publicationStmt', 'profileDesc', 'encodingDesc', 'sourceDesc',
    'langUsage', 'language', 'projectDesc', 'editorialDecl', 'correction',
    'normalization', 'hyphenation', 'segmentation', 'interpretation',
    'refsDecl', 'cRefPattern', 'charDecl', 'glyph', 'glyphName', 'figure',
    'graphic', 'add', 'c', 'del', 'ptr', 'ref', 'g'
)

SPELLCHOICES = ('orig', 'reg')
ABBRCHOICES = ('abbr', 'expan')

class TEItoHTMLTarget:
    def __init__(self, spellchoice='orig', abbrchoice='abbr'):
        # choice of original (<orig>) or regularized (<reg>) spelling
        self.spellchoice = spellchoice
        # choice of abbreviation (<abbr>) or expansion (<expan>)
        self.abbrchoice = abbrchoice
        # the stack of open tags (each tag is stored as a name-attrib pair)
        self.tags = []
        self.trb = ET.TreeBuilder()
        self.waiting_for = []
        self.lines = 0
        self.this_col_lines = 0
        self.max_col_lines = 0
        self.in_column = False
        self.in_header = True
        self.trb.start('div')

    def start(self, tag, attrib):
        if self.waiting_for:
            return
        if self.in_header:
            if tag not in HEADER_TAGS:
                self.in_header = False
                #self.open_tag('div', {'class':'col-xs-10'})
                self.open_tag('div', {'class':'printed_text_page'})
            else:
                return
        # dispatch to the proper tag_ function
        try:
            x = getattr(self, 'tag_' + tag)
            x(attrib)
        except AttributeError:
            pass
        # handle choice tags
        if tag in SPELLCHOICES and tag != self.spellchoice:
            self.waiting_for.append(tag)
        elif tag in ABBRCHOICES and tag != self.abbrchoice:
            self.waiting_for.append(tag)

    def tag_lb(self, attrib):
        if self.in_column:
            self.this_col_lines += 1
        else:
            self.lines += 1
        self.open_and_close_tag('br')

    def tag_head(self, attrib):
        self.open_tag('h4')

    def tag_hi(self, attrib):
        if attrib.get('rend') == 'italic':
            self.open_tag('span', {'class':'italic'})
        else:
            self.open_tag('span')

    def tag_foreign(self, attrib):
        # note that it is rend="italics", with an 's'
        if attrib.get('rend') == 'italics':
            self.open_tag('span', {'class':'italic'})
        else:
            self.open_tag('span')

    def tag_fw(self, attrib):
        if attrib.get('type') == 'catch' or attrib.get('type') == 'catchword':
            self.open_tag('div', {'class':'catch'})
        elif attrib.get('type') == 'sig':
            self.open_tag('div', {'class':'sig'})
        else:
            self.open_tag('div')

    def tag_pb(self, attrib):
        if attrib.get('type') != 'pdf':
            self.new_page()

    def tag_div(self, attrib):
        if attrib.get('rend') == 'center':
            self.open_tag('div', {'class':'center'})
        else:
            self.open_tag('div')

    def tag_p(self, attrib):
        if attrib.get('rend') == 'center':
            self.open_tag('p', {'class':'center'})
        else:
            self.open_tag('p')



    def tag_cb(self, attrib):
        self.in_column = True
        n_val = attrib.get('n')
        if n_val == '1':
            # value of '1' indicates start of column section
            self.open_tag('div')
            self.open_tag('div', {'class':'col-xs-6'})
        elif n_val == '':
            # empty value indicates end of column section
            self.in_column = False
            self.lines += self.max_col_lines
            self.max_col_lines = 0
            self.close_tag('div')
            self.close_tag('div')
        else:
            self.max_col_lines = max(self.max_col_lines, 
                                     self.this_col_lines)
            self.this_col_lines = 0
            self.close_tag('div')
            self.open_tag('div', {'class':'col-xs-6'})

    def end(self, tag):
        if self.waiting_for and tag == self.waiting_for[-1]:
            self.waiting_for.pop()
        if tag == 'head':
            self.close_tag('h4')
        elif tag == 'hi':
            self.close_tag('span')
        elif tag == 'fw':
            self.close_tag('div')
        elif tag == 'div':
            self.close_tag('div')
        elif tag == 'p':
            self.close_tag('p')
        elif tag == 'foreign':
            self.close_tag('span')

    def data(self, data):
        if not self.waiting_for and not self.in_header:
            self.trb.data(data)

    def open_tag(self, name, attribs={}):
        self.tags.append((name, attribs))
        self.trb.start(name, attribs)

    def open_and_close_tag(self, name, attribs={}):
        self.trb.start(name, attribs)
        self.trb.end(name)

    def close_tag(self, name):
        if len(self.tags) > 0:
            if self.tags[-1][0] == name:
                self.tags.pop()
                self.trb.end(name)
            else:
                msg  = 'trying to close <{}>, '.format(name)
                msg += 'but last tag opened was <{}>'.format(self.tags[-1][0])
                raise SyntaxError(msg)
        else:
            raise SyntaxError('got </{0}> before <{0}>'.format(name))

    def new_page(self):
        self.close_all_tags()
        self.lines = 0
        self.reopen_all_tags()

    def close(self):
        self.close_all_tags()
        out = self.trb.close()
        if out is not None:
            self.as_str = ET.tostring(out, encoding='unicode')
        else:
            self.as_str = ''
        self.trb = ET.TreeBuilder()

    def close_all_tags(self):
        # close all open tags
        for tag, _ in reversed(self.tags):
            self.trb.end(tag)

    def reopen_all_tags(self):
        # reopen the closed tags for the next page
        for tag, attribs in self.tags:
            self.trb.start(tag, attribs)

    def __str__(self):
        if not hasattr(self, 'as_str'):
            self.close()
        return self.as_str

def line_number_div(lines):
    line_nos = '\n'.join('{}<br/>'.format(i + 1) for i in range(lines))
    return '<div class="col-xs-2">{}</div>'.format(line_nos)

def magic_xml_to_html_target(data, *, spellchoice, abbrchoice):
    """Converts the XML string to HTMl and returns the TEItoHTMLTarget object
       used to parse. This is useful if you need to get at the individual pages
       of the document.
    """
    target = TEItoHTMLTarget(spellchoice, abbrchoice)
    parser = ET.XMLParser(target=target)
    parser.feed(data)
    parser.close()
    return target

def magic_xml_to_html(data, *, spellchoice, abbrchoice):
    """Converts the XML string to a corresponding HTML string."""
    return str(magic_xml_to_html_target(data, spellchoice=spellchoice, abbrchoice=abbrchoice))



## THE SCRIPT ##

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

def fromstring(data):
    return etree.XML(bytes(data, encoding='utf-8'))
def tostring(root):
    return etree.tostring(root, method='xml', encoding='unicode')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='convert TEI-encoded XML to HTML')
    parser.add_argument('infile', help='file to read XML from')
    parser.add_argument('outfile', nargs='?', help='file to write to')
    parser.add_argument('--preview', action='store_true', help='generate an HTML preview')
    parser.add_argument('--spellchoice', choices=['orig', 'reg-spacing', 'reg-spanish'], 
                                         default='orig')
    parser.add_argument('--abbrchoice', choices=['abbr', 'expan'], default='abbr')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--magic', action='store_true', help='use the Python ticha_magic parser')
    group.add_argument('--preprocess', action='store_true',help='apply the XSLT without paginating')
    args = parser.parse_args()
    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = ifsock.read()
    # decide which transform function to use, and what outfile name to generate
    infile_name = os.path.splitext(args.infile)[0]
    kwargs = {'abbrchoice':args.abbrchoice, 'spellchoice':args.spellchoice, 'textname':infile_name}
    if args.magic:
        data = magic_xml_to_html(data, **kwargs)
        outfile = args.outfile or infile_name + '.html'
    elif args.preprocess:
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
