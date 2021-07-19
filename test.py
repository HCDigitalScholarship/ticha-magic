import unittest
from lxml import etree
from src import *

class TestGenerateHTML(unittest.TestCase):

    # Show long diffs
    maxDiff = None

    def test_orig(self):

        tei_root = parse_xml_file('./tests/input.xml')
        xslt_path = "./xslt/test.xslt"
        flex_path = "./tests/flex_export.json"

        html_root = generate_html(
            tei_root,
            xslt_path=xslt_path,
            flex_path=flex_path,
            text="levanto_arte",
            spellchoice=SPELLCHOICE_ORIG,
            abbrchoice=ABBRCHOICE_ABBR
        )

        generated_html_string = etree.tostring(html_root, method="xml", encoding="unicode")

        with open("./tests/output.html", "r", encoding="utf-8") as f:
            expected_html_string = f.read()

        self.assertEqual(generated_html_string, expected_html_string)


    def test_reg(self):

        tei_root = parse_xml_file('./tests/input.xml')
        xslt_path = "./xslt/test.xslt"
        flex_path = "./tests/flex_export.json"

        html_root = generate_html(
            tei_root,
            xslt_path=xslt_path,
            flex_path=flex_path,
            text="levanto_arte",
            spellchoice=SPELLCHOICE_SPANISH,
            abbrchoice=ABBRCHOICE_ABBR
        )

        generated_html_string = etree.tostring(html_root, method="xml", encoding="unicode")

        with open("./tests/output_reg.html", "r", encoding="utf-8") as f:
            expected_html_string = f.read()

        self.assertEqual(generated_html_string, expected_html_string)


class TestGenerateOutline(unittest.TestCase):

    def test_outline(self):

        text = "levanto_arte"
        path = "./tests/input.xml"

        with open(path, "r", encoding="utf-8") as f:
            data = f.read()

        target = OutlineBuilder(text=text)
        parser = ET.XMLParser(target=target)
        parser.feed(data)
        root = target.close()
        generated_html_string = ET.tostring(root, encoding="unicode")

        with open("./tests/output_outline.html", "r", encoding="utf-8") as g:
            expected_html_string = g.read()

        self.assertEqual(generated_html_string, expected_html_string)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
