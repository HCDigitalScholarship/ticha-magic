#!/usr/bin/env python3
"""
Convert XML exports from FieldWorks Language Explorer (FLEx) to a more compact and
simple JSON format that the TEI FLEx inserter can use.

The JSON output is an object whose keys are the Zapotec words and whose values have the
form

  [
    {
      "section": str,
      "flex": {
        "name": str,
        "morphs": [str],
        "lex_glosses": [str],
        "en_gloss": str
       }
    },
    ...
  ]

where `section` is the section in the text where the word appears and `flex` contains
enough info to construct an annotation as an HTML element. Each value is a list because
a single word may have multiple annotations in different sections.
"""
import argparse
import os
import json
from collections import defaultdict
from lxml import etree

from flexify import strip_accents_and_spaces


def convert_flex_to_json(infile, outfile):
    """Read an XML file exported from FLEx and write its data to a JSON file."""
    with open(infile, 'r', encoding='utf-8') as ifsock:
        with open(outfile, 'w', encoding='utf-8') as ofsock:
            json_data = json.dumps(convert_flex_data_to_json(ifsock.read()), indent=1)
            ofsock.write(json_data)


def convert_flex_data_to_json(data):
    """
    Same as convert_flex_to_json, but takes a string argument and returns a dictionary
    (see the module docstring for a description of the dictionary's format).
    """
    ret = defaultdict(list)
    tr = etree.fromstring(data)
    # NOTE: This findall call relies on all the <interlinear-text> elements being direct
    # children of the root element.
    for text_element in tr.findall('interlinear-text'):
        text_name = get_text_name(text_element)
        for word_element in text_element.findall('.//phrases/word'):
            word_name = find_word_name(word_element)
            key = strip_accents_and_spaces(word_name)
            flex_object = make_flex_object(word_element)
            ret[key].append({'section': text_name, 'flex': flex_object})
    return ret


def get_text_name(element):
    """Find the name of a text within an <interlinear-text> element."""
    child = element.find(".//item[@type='title-abbreviation']")
    return child.text.lower().replace(' ', '')


def find_word_name(flex_element):
    """Given a <word> element, return the word name in Zapotec."""
    return ' '.join(word.text for word in flex_element.findall("words/word/item"))


def make_flex_object(flex_xml):
    """Load an XML <word> element into a FLExWord object."""
    name = find_word_name(flex_xml)
    # Get the morphemes and their lexical glosses.
    morphs = find_all_items(flex_xml, 'txt')
    lex_glosses = find_all_items(flex_xml, 'gls')
    # Get the literal English gloss.
    en_gloss = find_item(flex_xml, 'lit')
    return {
        'name': name, 'morphs': morphs, 'lex_glosses': lex_glosses, 'en_gloss': en_gloss
    }


def make_table_row(entries):
    return '<tr>' + ''.join('<td>' + e + '</td>' for e in entries) + '</tr>'


def find_item(parent, child_type):
    """
    Find the first <item> descendant of the parent element with a matching type
    attribute and return its text. If the first matching element has no text, the empty
    string is returned.
    """
    child = parent.find(".//item[@type='%s']" % child_type)
    if child is not None:
        if child.text:
            return child.text
    return ''


def find_all_items(parent, child_type):
    """
    Find the all <item> descendants of the parent element with a matching type attribute
    and return their texts as a list. <item> elements with no text appear in the list as
    empty strings.
    """
    children = parent.findall(".//morph/item[@type='%s']" % child_type)
    children_texts = [(child.text if child.text else '') for child in children]
    return children_texts


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
