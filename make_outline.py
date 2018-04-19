#!/usr/bin/env python3
"""Generate an HTML outline from a TEI-encoded XML document."""
import xml.etree.ElementTree as ET
import os
import argparse
from collections import namedtuple


known_namespaces = ['', 'http://www.tei-c.org/ns/1.0']

def tag_eq(tag,tagname):
    return any(tag == '{%s}%s' % (ns, tagname) for ns in known_namespaces)


def find_attr(attrs,attrname):
    for key in attrs:
        #are we expecting that keys do or don't have namespace prefix?
        if any(key == '{%s}%s' % (ns, attrname) for ns in known_namespaces):
            return attrs[key]


def xml_to_outline(data, text_prefix):
    """Given XML data as a string, return an HTML outline."""
    target = OutlineBuilder(text=text_prefix)
    parser = ET.XMLParser(target=target)
    parser.feed(data)
    root = target.close()
    return ET.tostring(root, encoding='unicode')


# class to represent Sections
Section = namedtuple('Section', ['number', 'title', 'page'])


class OutlineBuilder(ET.TreeBuilder):
    url = '/en/texts/{0.text}/{0.in_progress.page}/original'

    def __init__(self, *args, text='levanto', first_page=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.page = first_page
        self.in_progress = None
        self.get_title = False
        # self.number is always a list of strings, e.g. ['1', '2', '7'] for section 1.2.7
        self.number = ['1']
        super().start('div', {'class': 'index'})
        super().start('ul')

    def start(self, tag, attrs):
        if tag_eq(tag,'pb') and find_attr(attrs,'type') != 'pdf':
            self.page += 1
        elif tag_eq(tag,'div'):
            for key, value in attrs.items():
                if key.endswith('id') and value.startswith(self.text):
                    number = value[len(self.text):].split('.')
                    # write the previous section
                    self.write_section()
                    self.in_progress = Section(number, '', str(self.page))
                    break
        elif tag_eq(tag, 'head') and find_attr(attrs,'type') == 'outline':
            self.get_title = True

    def end(self, tag):
        if tag == 'head':
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


def infer_text_prefix(infile):
    """Infer the correct text prefix based on the file name."""
    if 'arte' in infile:
        if 'levanto' in infile:
            return 'levanto-arte'
        else:
            return 'arte'
    elif 'levanto' in infile:
        return 'levanto'
    else:
        return 'arte'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='XML file to read from')
    parser.add_argument('-o', '--outfile', nargs='?', help='file to write outline to')
    parser.add_argument('-t', '--text', nargs='?', help='short name of text, i.e. "levanto-arte".')
    args = parser.parse_args()

    if args.outfile:
        outfile = args.outfile
    else:
        outfile = os.path.splitext(args.infile)[0] + '_outline.html'
        print('Inferred output file', outfile)

    if args.text:
        text_prefix = args.text
    else:
        text_prefix = infer_text_prefix(args.infile)
        print('Inferred text prefix', text_prefix)

    with open(args.infile, 'r', encoding='utf-8') as ifsock:
        data = xml_to_outline(ifsock.read(), text_prefix=text_prefix)
    with open(outfile, 'w', encoding='utf-8') as ofsock:
        ofsock.write(data)
