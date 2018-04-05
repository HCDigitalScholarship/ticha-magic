#!/usr/bin/env python3
"""Convert TEI-encoded XML into human-readable HTML.

The conversion process goes through the following steps:

    preprocess: XML becomes pseudo-HTML (mostly HTML, but with the TEI <pb/> tags because it is too
                hard to turn these into <div>...</div> using XSLT).

    paginate: pseudo-HTML becomes real HTML, by fixing the <pb/> tags.

    flexify (optional): FLEx insertions from a separate XML file are inserted into the HTML.


In short:
    XML -> pseudo-HTML -> HTML -> HTML with FLEx

Use `convert_tei_file` or `convert_tei_data` to carry out the entire conversion in one fell swoop.
You can also invoke the intermediate functions `preprocess`, `paginate`, and `flexify`, but note
that for the sake of efficiency these only take XML/HTML trees as arguments, not strings or files.
"""
import sys
import os
import io
import re
import argparse
from collections import namedtuple
from contextlib import contextmanager

from lxml import etree, sax


def convert_tei_file(xml_file, out_file, xslt_file, *, flex_file=''):
    """Read a TEI-encoded XML document, convert it to HTML, and write the HTML data to the output
    file.

      xml_file: The path to a TEI-encoded XML document.
      html_file: The path to a file to which the HTML data will be written.
      xslt_file: The path to the XSLT stylesheet to be used in the conversion.
      flex_file: If provided, the path to the FLEx XML export containing annotations to be inserted
                 into the HTML.

    See the module docstring for details on the conversion process.
    """
    with open(xml_file, 'r', encoding='utf-8') as ifsock:
        with open(out_file, 'w', encoding='utf-8') as ofsock:
            ofsock.write(convert_tei_data(ifsock.read(), xslt_file, flex_file=flex_file))


def convert_tei_data(xml_data, xslt_file, *, flex_file=''):
    """Convert XML data (as a string) into HTML data (as a string). `xslt_file` and `flex_file` are
    the same as in convert_tei_file.
    """
    xml_root = etree.XML(bytes(xml_data, encoding='utf-8'))
    pseudo_html_root = preprocess(xml_root, xslt_file, abbrchoice='abbr', spellchoice='orig')
    html_root = paginate(pseudo_html_root, '')
    if flex_file:
        with open(flex_file, 'r', encoding='utf-8') as ifsock:
            flex_data = ifsock.read()
        flex_dict = FLExDict(flex_data)
        html_root = flexify(html_root, flex_dict)
    return etree.tostring(html_root, method='xml', encoding='unicode')


def preprocess(root, xslt_file, textname='', **kwargs):
    """Apply the XSLT stylesheet to the TEI-encoded XML document, but do not paginate."""
    xslt_transform = etree.XSLT(etree.parse(xslt_file).getroot())
    # Make sure that all of the keyword arguments are string-encoded, because we're about to pass
    # them to the XSLT stylesheet.
    for key, val in kwargs.items():
        if isinstance(val, str):
            kwargs[key] = etree.XSLT.strparam(val)
    return xslt_transform(root, **kwargs)


def paginate(root, text_name):
    """Paginate the TEI-encoded XML document. This entails removing all <pb/> elements and adding
    <div class="page">...</div> elements to wrap each page. This function should be called after
    preprocessing.
    """
    handler = TEIPager(text_name)
    sax.saxify(root, handler)
    return handler.etree


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
            msg = 'Tried to close <{}>'.format(qname)
            if self.real_tag_stack:
                msg += ', but last opened tag was <{}>'.format(self.real_tag_stack[-1])
            else:
                msg += ', but no tags have been opened'
            raise sax.SaxError(msg) from e


class TEIPager(AugmentedContentHandler):
    """A SAX parser that transforms <pb/> and <cb/> tags into <div>s that wrap pages and columns,
    respectively.
    """

    def __init__(self, text_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The tag stack is a stack of (ns_name, qname, attributes) tuples that represent the current
        # path in the tree.
        self.tag_stack = []
        self.page = 0
        self.line = 1
        self.text_name = text_name

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
        self.startElement('div', {'class': 'printed-text-page ' + self.text_name, 'data-n': page_no,
                                  'data-rvn': recto_verso_no})

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
                raise sax.SaxError(str(e) + 'on page {0.page}, line {0.line}'.format(self)) from e

    def closeAllTags(self):
        for ns_name, qname, _ in reversed(self.tag_stack):
            super().endElementNS(ns_name, qname)

    def reopenAllTags(self):
        for ns_name, qname, attributes in self.tag_stack:
            super().startElementNS(ns_name, qname, attributes)


### INSERT FLEX ANNOTATIONS INTO HTML ###
# At this level, the details of the FLEx annotations are abstracted away into a FLExDict which
# stores FLExWord objects that can be converted to HTML.

def flexify(html_root, flex_dict):
    """Insert FLEx annotations after every Zapotec word in the HTML root element."""
    handler = FLExParser(flex_dict)
    sax.saxify(html_root, handler)
    return handler.etree


class FLExParser(sax.ElementTreeContentHandler):
    """This parser adds the FLEx data to every Zapotec word contained in a <mark> tag.

    The reason it uses SAX parsing is that it needs to give each <mark> tag a new <span> parent tag,
    which is difficult to do with a DOM parser but relatively simple with a SAX one.

    Note that this parser will not preserve HTML comments, processing instructions, or anything else
    that is not a tag or text.
    """
    total = 0
    missed = 0

    def __init__(self, flex_dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_mark_tag = False
        self.flex_dict = flex_dict
        # the current word and section that the parser is processing
        self.word, self.section = '', ''
        self.tag_count = 0

    def startElement(self, tag, attributes=None):
        """A helper function that wraps startElementNS, without bothering with namespaces."""
        if attributes:
            attributes = {(None, key): val for key, val in attributes.items()}
        super().startElementNS((None, tag), tag, attributes)

    def endElement(self, tag):
        """A helper function that wraps endElementNS, without bothering with namespaces."""
        super().endElementNS((None, tag), tag)

    @contextmanager
    def E(self, tag, attributes=None):
        self.startElement(tag, attributes)
        yield
        self.endElement(tag)

    def startElementNS(self, ns_name, qname, attributes=None):
        if qname == 'mark':
            self.tag_count += 1
            # wrap each <mark> tag in a <span> for the popovers script
            self.startElement('span', {'class': 'popover-markup inline'})
            self.in_mark_tag = True
        elif qname == 'div':
            # div tags identifies the section in their id attributes
            new_section = attributes.get((None, 'id'))
            if new_section:
                # convert 2.01 to 2.1 etc.
                self.section = new_section.replace('.0', '.')
        super().startElementNS(ns_name, qname, attributes)

    def endElementNS(self, ns_name, qname):
        super().endElementNS(ns_name, qname)
        if qname == 'mark':
            if self.word:
                # add the FLEx data
                flex_word = FLExDict.lookup(self.section, self.word)
                # keep track of the missed words
                FLExParser.total += 1
                if not flex_word:
                    FLExParser.missed += 1
                with self.E('span', {'class': 'content hide inline'}):
                    self.createFLExWord(flex_word)
            self.endElement('span')
            self.in_mark_tag = False
            self.word = ''

    def createFLExWord(self, flex_word):
        if not flex_word:
            return
        with self.E('table'):
            with self.E('caption'):
                super().characters(flex_word.name)
            # if at least one morph and at least one gloss item is non-empty, add
            # the whole list to the table
            if any(flex_word.morphs) and any(flex_word.lex_glosses):
                self.createTableRow(flex_word.morphs)
                self.createTableRow(flex_word.lex_glosses)
            with self.E('td', {'colspan': str(len(flex_word.morphs))}):
                super().characters("'" + flex_word.lit_en_gloss + "'")

    def createTableRow(self, entries):
        with self.E('tr'):
            for entry in entries:
                with self.E('td'):
                    super().characters(entry)

    def characters(self, data):
        if self.in_mark_tag:
            # add the data to the current word
            self.word += data
        super().characters(data)


### LOAD FLEX DATA FROM XML INTO PYTHON OBJECTS ###
# At this level, you have to worry about the details of the XML file that the FLEx data is stored
# in. On the bright side, you don't have to care about HTML!


FLExWord = namedtuple('FLExWord', ['name', 'lex_glosses', 'morphs', 'lit_en_gloss'])


class FLExDict:
    """A dictionary-like object that can retrieve FLEx data (as FLExWord objects) when given a
    section title and a word. Note that this class is not intended to be instantiated; just use the
    FLExDict.lookup function when you need to look up a word.

    Internally, the dictionary keys are section titles, and each section title maps to another
    dictionary (actually a defaultdict so that missed matches return an empty string) which maps
    from word names to FLEx data. This is because the same word may appear in multiple sections with
    different FLEx data, so the dictionary has to be partitioned. However, this is an implementation
    detail that should not concern you - just use the lookup method!
    """
    dct = {}

    def __init__(self, data):
        self.load(data)

    @classmethod
    def load(cls, data):
        """Load the FLEx linguistic data from the arte_flex.xml file into a dictionary which can
        then be queried by the lookup method.
        """
        tr = etree.fromstring(data)
        # note that this findall call relies on all the <interlinear-text> elements being direct
        # children of the root element
        for text_element in tr.findall('interlinear-text'):
            text_name = get_text_name(text_element)
            # make a new dict for the current section
            cls.dct[text_name] = {}
            # we are only concerned <word> elements that are children of <phrases> elements
            for word_element in text_element.findall('.//phrases/word'):
                word_name = find_word_name(word_element)
                flex_word = xml_to_flex_word(word_element)
                key = strip_accents_and_spaces(word_name)
                if key:
                    cls.dct[text_name][key] = flex_word

    @classmethod
    def lookup(cls, section, word):
        """Look up a word in a certain section of a dictionary. The return value is a FLExWord
        object, or the empty string if no match is found.
        """
        word = strip_accents_and_spaces(word)
        # try to find the correct section dictionary
        if section in cls.dct:
            return cls.dct[section].get(word)
        else:
            # look for inexact matches with the dictionary key
            best_match = ''
            best_match_dict = {}
            for key, val in cls.dct.items():
                if section.startswith(key):
                    # longer matches are better
                    if len(key) > len(best_match):
                        best_match = key
                        best_match_dict = val
            return best_match_dict.get(word)


def xml_to_flex_word(flex_xml):
    """Load an XML <word> element into a FLExWord object."""
    # get the morphemes and their lexical glosses
    morphs = find_all_items(flex_xml, 'txt')
    lex_glosses = find_all_items(flex_xml, 'gls')
    # get the literal English gloss
    lit_en_gloss = find_item(flex_xml, 'lit')
    return FLExWord(name=find_word_name(flex_xml), morphs=morphs, lex_glosses=lex_glosses,
                    lit_en_gloss=lit_en_gloss)


def find_item(parent, child_type):
    """Find the first <item> descendant of the parent element with a matching type attribute and
    return its text. If the first matching element has no text, the empty string is returned.
    """
    child = parent.find(".//item[@type='%s']" % child_type)
    if child is not None:
        if child.text:
            return child.text
    return ''


def find_all_items(parent, child_type):
    """Find the all <item> descendants of the parent element with a matching type attribute and
    return their texts as a list. <item> elements with no text appear in the list as empty strings.
    """
    children = parent.findall(".//morph/item[@type='%s']" % child_type)
    children_texts = [(child.text if child.text else '') for child in children]
    return children_texts


def find_word_name(flex_element):
    """Given a <word> element, return the word name in Zapotec."""
    return ' '.join(word.text for word in flex_element.findall("words/word/item"))


def get_text_name(element):
    """Find the name of a text within an <interlinear-text> element."""
    child = element.find(".//item[@type='title-abbreviation']")
    return child.text.lower().replace(' ', '')


def strip_accents_and_spaces(s):
    """Remove whitespace, punctuation and accents from accented characters in s, convert to
    lowercase, and remove letters in between square brackets.
    """
    accent_dict = {
        'ǎ': 'a', 'ã': 'a', 'á': 'a', 'ä': 'a', 'à': 'a', 'ã': 'a', 'ā': 'a', 'é': 'e', 'ě': 'e',
        'è': 'e', 'ē': 'e', 'ï': 'i', 'í': 'i', 'î': 'i', 'ì': 'i', 'ó': 'o', 'ö': 'o', 'ǒ': 'o',
        'ô': 'o', 'õ': 'o', 'q̃': 'q', 'q̃̃': 'q', 'q~': 'que', 'ſ': 's', 'û': 'u', 'ǔ': 'u', 'ú': 'u'
    }
    for key, val in accent_dict.items():
        s = s.replace(key, val)
    # Remove whitespace.
    s = ''.join(s.split())
    s = s.lower()
    # Remove characters between square brackets.
    s = re.sub(r'\[\w+\]', '', s)
    # Remove punctuation.
    punctuation_set = set([',', '.', '[', ']', "'", '?', '*', '’', '-'])
    s = ''.join(char for char in s if char not in punctuation_set)
    return s


def tag_eq(tag_in_document, tag_to_check):
    """Compare equality of tags ignoring namespaces. Note that this is not commutative."""
    return tag_in_document == tag_to_check or tag_in_document.endswith(':' + tag_to_check)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    parser.add_argument('-o', '--outfile', required=True)

    args = parser.parse_args()
    convert_tei_file(args.infile, args.outfile, 'xslt/base.xslt')
