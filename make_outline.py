"""Generate an HTML outline from a TEI-encoded XML document."""
import xml.etree.ElementTree as ET
import os
import argparse
from collections import namedtuple


def xml_to_outline(data, textname):
    """Given XML data as a string, return an HTML outline."""
    target = OutlineBuilder(textname=textname)
    parser = ET.XMLParser(target=target)
    parser.feed(data)
    root = target.close()
    return ET.tostring(root, encoding='unicode')


# class to represent Sections
Section = namedtuple('Section', ['number', 'title', 'page'])


KNOWN_NAMESPACES = ('', '{http://www.tei-c.org/ns/1.0}', '{http://www.w3.org/XML/1998/namespace}')
def tag_eq(tag_from_doc, tag_literal):
    """Return True if `tag_from_doc` matches the `tag_literal` in any known namespace."""
    return any(tag_from_doc == ns + tag_literal for ns in KNOWN_NAMESPACES)

def get_xml_attr(attrs, key_literal):
    """Fetch the key from the attrs dictionary, trying all known namespaces."""
    for ns in KNOWN_NAMESPACES:
        try:
            return attrs[ns + key_literal]
        except KeyError:
            pass
    return None


class OutlineBuilder(ET.TreeBuilder):
    url = '/en/texts/{0.textname}/{0.in_progress.page}/original'

    def __init__(self, *args, textname, first_page=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.textname = textname
        self.page = first_page
        self.in_progress = None
        self.get_title = False
        # self.number is always a list of strings, e.g. ['1', '2', '7'] for section 1.2.7
        self.number = ['1']
        super().start('div', {'class': 'index'})
        super().start('ul')

    def start(self, tag, attrs):
        if tag_eq(tag, 'pb') and get_xml_attr(attrs, 'type') != 'pdf':
            self.page += 1
        elif tag_eq(tag, 'div'):
            div_id = get_xml_attr(attrs, 'id')
            if div_id is not None and div_id.startswith(self.textname):
                number = div_id[len(self.textname):].split('.')
                # write the previous section
                self.write_section()
                self.in_progress = Section(number, '', str(self.page))
        elif tag_eq(tag, 'head') and get_xml_attr(attrs, 'type') == 'outline':
            self.get_title = True

    def end(self, tag):
        if tag_eq(tag, 'head'):
            self.get_title = False

    def data(self, data):
        if self.get_title:
            if self.in_progress:
                new_title = self.in_progress.title + data
                self.in_progress = self.in_progress._replace(title=new_title)

    def close(self):
        self.write_section()
        super().end('ul')
        super().end('div')
        return super().close()

    def write_section(self):
        if self.in_progress is not None:
            # check if any nested lists need to be opened/closed based on the section number
            how_many_to_close = len(self.number) - len(self.in_progress.number)
            if how_many_to_close > 0:
                for i in range(how_many_to_close):
                    super().end('ul')
            elif how_many_to_close < 0:
                how_many_to_open = -how_many_to_close
                for i in range(len(self.number), len(self.number) + how_many_to_open - 1):
                    super().start('ul')
                    super().start('li')
                    super().data('.'.join(self.in_progress.number[i:]))
                    super().end('li')
                super().start('ul', {'id': 'section'+'.'.join(self.number)})
            super().start('li')
            super().start('a', {'href': self.url.format(self)})
            # i.e., 1.3.1 Licencia
            super().data('.'.join(self.in_progress.number) + ' ' + self.in_progress.title)
            super().end('a')
            super().end('li')
            self.number = self.in_progress.number
