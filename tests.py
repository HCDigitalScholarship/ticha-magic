"""
Test the ticha_magic script.

The test runner loads an XML file, converts it to HTML using ticha_magic, and then compares it to
a stored answer key file.
"""
from ticha_magic import convert_tei_data


with open('tests/input.xml', 'r') as infile:
    xml_data = infile.read()

with open('tests/output.html', 'r') as infile:
    answer_key = infile.read()

html_data = convert_tei_data(xml_data, 'xslt/test.xslt', flex_file='tests/flex_export.json')
if html_data != answer_key:
    print('FAILURE!', end=' ')
    print('Please inspect failed_output.html and compare it to the answer key at tests/output.html')
    with open('failed_output.html', 'w') as f:
        f.write(html_data)
else:
    print('Success!')
