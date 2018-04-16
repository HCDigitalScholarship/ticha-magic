"""
The new architecture of the FLEx inserter:

    1. Convert the FLEx XML export into a stripped-down JSON file that includes only the information
       that is needed for insertion (which is just the word, the section it appears in, and the
       HTML text of the popover element to be inserted).
    2. Load the JSON file into a Python dictionary and insert FLEx annotations into the text as
       before.


Should the JSON file be persistent, or created every time?

  Probably better for it to be persistent since creating it will be probably be an expensive
  operation. On the other hand, if it's persistent we run the risk of accidentally using an old JSON
  file after the XML has been exported, which could give confusing results until we figure out what
  we did wrong.


What should the interface be?

    1. The user supplies only the XML export, and the script creates the JSON file.
    2. The user supplies either the XML export or the JSON file, and the script just does the right
       thing.
    3. The user supplies only the JSON file; a separate script exists to convert the XML to JSON.
       I'm leaning towards this because it makes every step explicit. It's not like we get new FLEx
       exports very often so adding the extra step of converting XML to JSON explicitly is only a
       small price.
"""
import json
from contextlib import contextmanager
from lxml import sax


def flexify(html_root, flex_file):
    """Insert FLEx annotations after every Zapotec word in the HTML root element."""
    with open(flex_file, 'r', encoding='utf-8') as f:
        flex_dict = json.load(f)
    handler = FLExParser(flex_dict)
    sax.saxify(html_root, handler)
    print('Processed {0.total} word(s), missed {0.missed}'.format(handler))
    return handler.etree


class FLExParser(sax.ElementTreeContentHandler):
    """This parser adds the FLEx data to every Zapotec word contained in a <mark> tag.

    The reason it uses SAX parsing is that it needs to give each <mark> tag a new <span> parent tag,
    which is difficult to do with a DOM parser but relatively simple with a SAX one.

    Note that this parser will not preserve HTML comments, processing instructions, or anything else
    that is not a tag or text.
    """

    def __init__(self, flex_dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.in_mark_tag = False
        self.flex_dict = flex_dict
        self.total = 0
        self.missed = 0
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
                flex_word = lookup(self.flex_dict, self.section, self.word)
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
            # If at least one morph and at least one gloss item is non-empty, add the whole list to
            # the table.
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
    """Look up a word that appears in a certain section of the text in the FLEx dictionary. Return
    the word as a JSON object (see the docstring of flexml_to_json.py for the exact format).
    """
    return dict(name='placeholder', morphs=[], lex_glosses=[], en_gloss='test word')
