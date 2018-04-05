"""Define common functions used by multiple modules in the repository."""
import os


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
