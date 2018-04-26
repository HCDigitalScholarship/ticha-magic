"""Define common functions used by multiple modules in the repository."""
import os
import re


def tag_eq(tag_in_document, tag_to_check):
    """Compare equality of tags ignoring namespaces. Note that this is not commutative."""
    return tag_in_document == tag_to_check or tag_in_document.endswith(':' + tag_to_check)


def get_output_file(input_file):
    """Given an input file, generate the name of a corresponding output file."""
    return os.path.splitext(input_file)[0] + '.html'


def get_xslt_file(input_file):
    """Given the file path of a TEI text, infer the proper XSLT stylesheet to use."""
    if 'arte' in input_file and 'levanto' in input_file:
        return 'xslt/levanto_arte.xslt'
    elif 'arte' in input_file:
        return 'xslt/arte.xslt'
    else:
        return 'xslt/base.xslt'


def strip_accents_and_spaces(s):
    """
    Remove whitespace, punctuation and accents from accented characters in s, convert to lowercase,
    and remove letters in between square brackets.
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
