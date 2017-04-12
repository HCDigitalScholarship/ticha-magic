#!/usr/bin/env python3
import sys
import os
from lxml import etree, sax

class TEIPager(sax.ElementTreeContentHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_text = False
        self.tag_stack = []

    def startElementNS(self, ns_name, qname, attributes=None):
        if qname == 'text':
            self.in_text = True
            super().startElementNS(ns_name, qname, attributes)
            # this line never actually produces a <div class="printed_text_page"> element in the
            # output
            self.startElementNS((None, 'div'), 'div', {(None, 'class'):'printed_text_page'})
        elif qname == 'pb':
            self.closeAllTags()
            self.reopenAllTags()
        else:
            if self.in_text:
                self.tag_stack.append( (ns_name, qname, attributes) )
            super().startElementNS(ns_name, qname, attributes)

    def endElementNS(self, ns_name, qname):
        if qname == 'text':
            self.in_text = False
            super().endElementNS((None, 'div'), 'div')
            super().endElementNS(ns_name, qname)
        elif qname != 'pb':
            if self.in_text:
                self.tag_stack.pop()
            super().endElementNS(ns_name, qname)

    def closeAllTags(self):
        for ns_name, qname, _ in reversed(self.tag_stack):
            super().endElementNS(ns_name, qname)

    def reopenAllTags(self):
        for ns_name, qname, attributes in self.tag_stack:
            super().startElementNS(ns_name, qname, attributes)

def xml_to_html(xml_data):
    html_root = xml_to_html_root(xml_data)
    return etree.tostring(html_root, method='html', encoding='unicode')

def xml_to_html_root(xml_data):
    xml_root = etree.XML(xml_data)
    handler = TEIPager()
    sax.saxify(xml_root, handler)
    xslt_root = etree.parse('transform.xslt').getroot()
    transform = etree.XSLT(xslt_root)
    return transform(handler.etree)

if __name__ == '__main__':
    if 2 <= len(sys.argv) <= 3:
        in_path = sys.argv[1]
        if len(sys.argv) == 2:
            name, ext = os.path.splitext(in_path)
            out_path = name + '_from_xslt.html'
        else:
            out_path = sys.argv[2]
        with open(in_path, 'r') as ifsock:
            data = ifsock.read()
        html_root = xml_to_html_root(data)
        html_root.write(out_path, method='html')
    else:
        print('Usage: ./xslt_magic.py <XML filepath> <optional HTML output path>')