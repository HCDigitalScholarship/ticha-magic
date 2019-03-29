"""
Test the ticha_magic script.

The test runner loads an XML file, converts it to HTML using ticha_magic, and then
compares it to a stored answer key file.
"""
from ticha_magic import convert_tei_data
from make_outline import xml_to_outline

INPUT = 'tests/input.xml'
ANSWER_KEY = 'tests/output.html'
OUTLINE_ANSWER_KEY = 'tests/outline_output.html'
FAILED = 'failed.html'
FAILED_OUTLINE = 'failed_outline.html'

XSLT = 'xslt/test.xslt'
FLEX = 'tests/flex_export.json'


with open(INPUT, 'r') as infile:
    xml_data = infile.read()

with open(ANSWER_KEY, 'r') as infile:
    answer_key = infile.read()

with open(OUTLINE_ANSWER_KEY, 'r') as infile:
    outline_answer_key = infile.read()

html_data = convert_tei_data(xml_data, XSLT, flex_file=FLEX)
if html_data != answer_key:
    print('FAILURE!', end=' ')
    print(
        'Please inspect {} and compare it to the answer key at {}'.format(
            FAILED, ANSWER_KEY
        )
    )
    with open(FAILED, 'w') as f:
        f.write(html_data)
else:
    outline_data = xml_to_outline(xml_data, 'levanto')
    if outline_data != outline_answer_key:
        print('FAILURE!', end=' ')
        print(
            'Please inspect {} and compare it to the answer key at {}'.format(
                FAILED_OUTLINE, OUTLINE_ANSWER_KEY
            )
        )
        with open(FAILED_OUTLINE, 'w') as f:
            f.write(outline_data)
    else:
        print('Success!')
