import re
from collections import namedtuple
from contextlib import contextmanager

from lxml import etree, sax

from common import tag_eq


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
        # The current word and section that the parser is processing.
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
