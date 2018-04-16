#!/usr/bin/env python3
"""Convert XML exports from FieldWorks Language Explorer (FLEx) to a more compact and simple JSON
format that the TEI FLEx inserter can use.

The JSON output is an object whose keys are the Zapotec words and whose values have the form

  [{"section": "...", "popover_html": "..." }, ... ]

where `section` is the section in the text where the word appears and `popover_html` is the full
annotation in HTML format, as a string. Each value is a list because a single word may have multiple
annotations in different sections.
"""
import re
import argparse
import os
import json
from collections import defaultdict
from lxml import etree


def convert_flex_to_json(infile, outfile):
    """Read an XML file exported from FLEx and write its data to a JSON file."""
    with open(infile, 'r', encoding='utf-8') as ifsock:
        with open(outfile, 'w', encoding='utf-8') as ofsock:
            ofsock.write(json.dumps(convert_flex_data_to_json(ifsock.read())))


def convert_flex_data_to_json(data):
    """Same as convert_flex_to_json, but takes a string argument and returns a dictionary (see the
    module docstring for a description of the dictionary's format)."""
    ret = defaultdict(list)
    tr = etree.fromstring(data)
    # NOTE: This findall call relies on all the <interlinear-text> elements being direct children of
    # the root element.
    for text_element in tr.findall('interlinear-text'):
        text_name = get_text_name(text_element)
        for word_element in text_element.findall('.//phrases/word'):
            word_name = find_word_name(word_element)
            key = strip_accents_and_spaces(word_name)
            popover_html = make_popover_html(word_element)
            ret[key].append({'section': text_name, 'popover_html': popover_html})
    return ret


def get_text_name(element):
    """Find the name of a text within an <interlinear-text> element."""
    child = element.find(".//item[@type='title-abbreviation']")
    return child.text.lower().replace(' ', '')


def find_word_name(flex_element):
    """Given a <word> element, return the word name in Zapotec."""
    return ' '.join(word.text for word in flex_element.findall("words/word/item"))


def make_popover_html(flex_xml):
    """Load an XML <word> element into a FLExWord object."""
    name = find_word_name(flex_xml)
    # Get the morphemes and their lexical glosses.
    morphs = find_all_items(flex_xml, 'txt')
    lex_glosses = find_all_items(flex_xml, 'gls')
    # Get the literal English gloss.
    lit_en_gloss = find_item(flex_xml, 'lit')
    if any(morphs) and any(lex_glosses):
        rows = make_table_row(morphs) + make_table_row(lex_glosses)
    else:
        rows = ''
    html_gloss = '<td colspan="{}">\'{}\'</td>'.format(len(morphs), lit_en_gloss)
    return '<table><caption>' + name + '</caption>' + rows + html_gloss;


def make_table_row(entries):
    return '<tr>' + ''.join('<td>' + e + '</td>' for e in entries) + '</tr>'


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    parser.add_argument('-o', '--outfile')
    args = parser.parse_args()

    if args.outfile:
        outfile = args.outfile
    else:
        outfile = os.path.splitext(args.infile)[0] + '.json'

    convert_flex_to_json(args.infile, outfile)
