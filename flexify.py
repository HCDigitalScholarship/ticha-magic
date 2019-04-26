"""
Insert FLEx annotations into HTML. Works on the output of the pseudo-HTML -> HTML stage
in the ticha_magic converter. Users of this library should only use the flexify()
function.
"""
import json
from contextlib import contextmanager
from lxml import sax

from common import strip_accents_and_spaces


def flexify(html_root, flex_file):
    """Insert FLEx annotations after every Zapotec word in the HTML root element."""
    with open(flex_file, 'r', encoding='utf-8') as f:
        flex_dict = json.load(f)
    print('{} words in the FLEx dictionary'.format(len(flex_dict)))
    handler = FLExParser(flex_dict)
    sax.saxify(html_root, handler)
    print('Processed {0.total} word(s), missed {0.missed}'.format(handler))
    return handler.etree


class FLExParser(sax.ElementTreeContentHandler):
    """
    This parser adds the FLEx data to every Zapotec word contained in a <mark> tag.

    The reason it uses SAX parsing is that it needs to give each <mark> tag a new <span>
    parent tag, which is difficult to do with a DOM parser but relatively simple with a
    SAX one.

    Note that this parser will not preserve HTML comments, processing instructions, or
    anything else that is not a tag or text.
    """

    def __init__(self, flex_dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_mark_tag = False
        self.flex_dict = flex_dict
        self.total = 0
        self.missed = 0
        # The current word and section that the parser is processing.
        self.word, self.section = '', ''

    def startElement(self, tag, attributes=None):
        """
        A helper function that wraps startElementNS, without bothering with namespaces.
        """
        if attributes:
            attributes = {(None, key): val for key, val in attributes.items()}
        super().startElementNS((None, tag), tag, attributes)

    def endElement(self, tag):
        """
        A helper function that wraps endElementNS, without bothering with namespaces.
        """
        super().endElementNS((None, tag), tag)

    @contextmanager
    def E(self, tag, attributes=None):
        self.startElement(tag, attributes)
        yield
        self.endElement(tag)

    def startElementNS(self, ns_name, qname, attributes=None):
        if qname == 'mark':
            # Wrap each <mark> tag in a <span> for the popovers script.
            self.startElement('span', {'class': 'popover-markup inline'})
            self.in_mark_tag = True
        elif qname == 'div':
            # <div> tags identify their section in their id attributes.
            new_section = attributes.get((None, 'id'))
            if new_section:
                # Convert 2.01 to 2.1 etc.
                self.section = new_section.replace('.0', '.')
        super().startElementNS(ns_name, qname, attributes)

    def endElementNS(self, ns_name, qname):
        super().endElementNS(ns_name, qname)
        if qname == 'mark':
            if self.word:
                # Add the FLEx data.
                flex_word = lookup(self.flex_dict, self.word, self.section)
                # Keep track of the missed words.
                self.total += 1
                if not flex_word:
                    self.missed += 1
                with self.E('span', {'class': 'content hide inline'}):
                    self.createFLExWord(flex_word)
            self.endElement('span')
            self.in_mark_tag = False
            self.word = ''

    def createFLExWord(self, flex_word):
        if not flex_word:
            return
        name = flex_word['name']
        morphs = flex_word['morphs']
        lex_glosses = flex_word['lex_glosses']
        en_gloss = flex_word['en_gloss']
        with self.E('table'):
            with self.E('caption'):
                super().characters(name)
            # If at least one morph and at least one gloss item is non-empty, add the
            # whole list to the table.
            if any(morphs) and any(lex_glosses):
                self.createTableRow(morphs)
                self.createTableRow(lex_glosses)
            with self.E('td', {'colspan': str(len(morphs))}):
                super().characters("'" + en_gloss + "'")

    def createTableRow(self, entries):
        with self.E('tr'):
            for entry in entries:
                with self.E('td'):
                    super().characters(entry)

    def characters(self, data):
        if self.in_mark_tag:
            # Add the data to the current word.
            self.word += data
        super().characters(data)


def lookup(flex_dict, word, section):
    """
    Look up a word that appears in a certain section of the text in the FLEx dictionary.
    Return the word as a JSON object (see the docstring of flexml_to_json.py for the
    exact format).
    """
    word = strip_accents_and_spaces(word)
    best_match = ''
    best_match_ret = {}
    for found_word in flex_dict.get(word, []):
        found_section = found_word['section']
        if found_section == section:
            return found_word['flex']
        # Sometimes the sections in the actual text are more precise than the ones in
        # the FLEx export (i.e. the text will list 2.3.1.4 while the FLEx will only have
        # 2.3) so we look for sections that partially match.
        elif section.startswith(found_section):
            if len(found_section) > len(best_match):
                best_match = found_section
                best_match_ret = found_word['flex']
    return best_match_ret
