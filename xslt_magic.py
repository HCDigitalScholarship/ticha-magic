import sys
import os
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


def xml_to_html(xml_root):
    return paginate(preprocess(xml_root))

def xml_to_html_from_str(data):
    root = xml_from_string(data)
    return string_from_xml(paginate(preprocess(root)))

def preprocess(root):
    xslt_transform = etree.XSLT(etree.parse(XSLT_PATH).getroot())
    return xslt_transform(root)

def preprocess_from_str(data):
    root = xml_from_string(data)
    return string_from_xml(preprocess(root))

def paginate(root):
    # I do not understand why it is necessary to cast to bytes here
    handler = TEIPager()
    sax.saxify(root, handler)
    return handler.etree


def tag_eq(tag_in_document, tag_to_check):
    """Compare equality of tags ignoring namespaces. Not that this is not commutative."""
    return tag_in_document == tag_to_check or tag_in_document.endswith(':' + tag_to_check)

def xml_from_string(data, encoding='utf-8'):
    return etree.XML(bytes(data, encoding=encoding))

def string_from_xml(root, method='xml', encoding='unicode'):
    return etree.tostring(root, method=method, encoding=encoding)
