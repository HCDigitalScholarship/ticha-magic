import xml.etree.ElementTree as ET
from collections import namedtuple
from lxml import etree, sax
import logging
from .flexify import flexify
import re
from .preview_templates import OUTLINE_PREVIEW_TEMPLATE

# Possible settings for the <choice> tag in TEI.
SPELLCHOICE_ORIG = "orig"
SPELLCHOICE_SPANISH = "reg-spanish"
SPELLCHOICE_SPACING = "reg-spacing"
ABBRCHOICE_ABBR = "abbr"
ABBRCHOICE_EXPAN = "expan"


TEXT_PARAMS = {
    "levanto-arte": {
        "xslt_path": "xslt/levanto-arte.xslt",
        "flex_path": ""
    },
    "levanto-cathecismo": {
        "xslt_path": "xslt/levanto-cathecismo.xslt",
        "flex_path": ""
    },
    "cordova-arte": {
        "xslt_path": "xslt/cordova-arte.xslt",
        "flex_path": "cordova-arte_flex_export.json"
    },
    "aguero-miscelaneo": {
        "xslt_path": "xslt/aguero-miscelaneo.xslt",
        "flex_path": ""
    },
    "Te744": {
        "xslt_path": "xslt/Te744.xslt",
        "flex_path": ""
    },
    "Te744T": {
        "xslt_path": "xslt/Te744T.xslt",
        "flex_path": ""
    }
}


class AugmentedContentHandler(sax.ElementTreeContentHandler):
    """
    Augment the lxml implementation to support better error messages and provide the
    useful (though namespace-unaware) startElement and endElement methods.

    This class doesn't do anything interesting itself other than provide the above
    services to TEIPager, which is a subclass.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The real tag stack keeps track of the actual tags that are currently open. It
        # is used to print more helpful error messages.
        self.real_tag_stack = []

    def startElement(self, name, attributes=None):
        # In vanilla lxml.sax, every attribute is a (namespace, key) pair, which is a
        # little annoying to have to write every time when you're not using a namespace.
        # This function takes a regular dictionary and adds the empty namespace to every
        # attribute.
        if attributes is not None:
            attributes = {(None, key): val for key, val in attributes.items()}
        AugmentedContentHandler.startElementNS(self, (None, name), name, attributes)

    def endElement(self, name):
        AugmentedContentHandler.endElementNS(self, (None, name), name)

    def startElementNS(self, ns_name, qname, attributes=None):
        self.real_tag_stack.append(qname)
        super().startElementNS(ns_name, qname, attributes)

    def endElementNS(self, ns_name, qname):
        try:
            super().endElementNS(ns_name, qname)
            self.real_tag_stack.pop()
        except sax.SaxError as e:
            msg = f"Tried to close <{qname}>"
            if self.real_tag_stack:
                msg += f", but last opened tag was <{self.real_tag_stack[-1]}>. Tag stack: {self.real_tag_stack}"
            else:
                msg += ", but no tags have been opened"
            raise sax.SaxError(msg) from e


class TEIPager(AugmentedContentHandler):
    """
    A SAX parser that transforms <pb/> and <cb/> tags into <div>s that wrap pages and
    columns, respectively.
    """

    def __init__(self, text_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The tag stack is a stack of (ns_name, qname, attributes) tuples that represent
        # the current path in the tree.
        self.tag_stack = []
        self.page = 0
        self.line = 1
        self.text_name = text_name

    def startElementNS(self, ns_name, qname, attributes=None):
        if tag_eq(qname, "pb"):
            if attributes.get((None, "type")) != "pdf":
                recto_verso_no = attributes.get((None, "n"), "")
                self.handlePageBreak(recto_verso_no)
        elif tag_eq(qname, "cb"):
            n = attributes.get((None, "n"))
            self.handleColumnBreak(n)
        elif tag_eq(qname, "body"):
            self.startElement("div")
            self.startNewPageDiv(str(self.page), "0")
        else:
            if tag_eq(qname, "br"):
                self.line += 1
            self.tag_stack.append((ns_name, qname, attributes))
            super().startElementNS(ns_name, qname, attributes)

    def handlePageBreak(self, recto_verso_no):
        self.line = 1
        self.page += 1
        self.closeAllTags()
        self.endElement("div")
        self.startNewPageDiv(str(self.page), recto_verso_no)
        self.reopenAllTags()

    def startNewPageDiv(self, page_no, recto_verso_no):
        attrs = {
            "class": "printed-text-page " + self.text_name,
            "data-n": page_no,
            "data-rvn": recto_verso_no,
        }
        self.startElement("div", attrs)

    def handleColumnBreak(self, n):
        lastTag = self.tag_stack[-1][1]
        if not lastTag == "div":
            raise sax.SaxError(f"Column break (<cb.../>) must be inside a <div> tag: page {self.page}, line {self.line}")
        if n == "1":
            # A value of '1' indicates start of column section.
            self.startElement("div")
            self.startElement("div", {"class": "col-xs-6"})
        elif n == "":
            # An empty value indicates end of column section.
            self.endElement("div")
            self.endElement("div")
        else:
            self.endElement("div")
            self.startElement("div", {"class": "col-xs-6"})

    def endElementNS(self, ns_name, qname):
        # Ignore self-closing <pb> and <cb> tags; they were already handled by
        # startElementNS.
        if tag_eq(qname, "body"):
            self.endElement("div")
            self.endElement("div")
        elif not tag_eq(qname, "pb") and not tag_eq(qname, "cb"):
            closes = self.tag_stack.pop()
            try:
                super().endElementNS(ns_name, qname)
            except sax.SaxError as e:
                raise sax.SaxError(
                    str(e) + f"on page {self.page}, line {self.line}"
                ) from e

    def closeAllTags(self):
        for ns_name, qname, _ in reversed(self.tag_stack):
            super().endElementNS(ns_name, qname)

    def reopenAllTags(self):
        for ns_name, qname, attributes in self.tag_stack:
            super().startElementNS(ns_name, qname, attributes)


def paginate(pseudo_html_root, text_name):
    """
    Paginate the output of the XSLT transformation. This entails removing all <pb/>
    elements and adding <div class="page">...</div> elements to wrap each page. The
    output of this function is valid HTML.
    """
    # TODO [2019-04-26]: Is text_name necessary for anything? It becomes a CSS class
    # that's on the page <div>'s, so we should check the Ticha website's stylesheets
    # to see if it's ever targeted.
    handler = TEIPager(text_name)
    sax.saxify(pseudo_html_root, handler)
    return handler.etree


def tag_eq(tag_in_document, tag_to_check):
    """
    Compare equality of tags ignoring namespaces.

      tag_in_document: the value of a tag encountered while parsing a document, which
                       may begin with a namespace.

      tag_to_check: an XML/HTML tag as a literal string which MAY NOT begin with a
                    namespace.

    Note that this is not commutative.
    """
    return tag_in_document == tag_to_check or tag_in_document.endswith(
        ':' + tag_to_check
    )


KNOWN_NAMESPACES = ["", "http://www.tei-c.org/ns/1.0"]


def outline_tag_eq(tag, tagname):
    """
    Return True if the tags are equal regardless of namespace. `tagname` should be a
    constant string with no namespace prefix, e.g. 'div'.
    """
    return tag == tagname or any(
        tag == f"{{{ns}}}{tagname}" for ns in KNOWN_NAMESPACES
    )


def find_attr(attrs, attrname):
    """
    Compute attrs.get(attrname), except do not consider namespaces when looking for
    matches in the dictionary, so find_attr(attrs, 'type') and find_attr('{...}type')
    are equivalent.
    """
    for key in attrs:
        if key == attrname or any(
            key == f"{{{ns}}}{attrname}" for ns in KNOWN_NAMESPACES
        ):
            return attrs[key]
    return None


Section = namedtuple("Section", ["number", "title", "page"])


class OutlineBuilder(ET.TreeBuilder):
    def __init__(self, *args, text, first_page=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.page = first_page
        self.in_progress = None
        self.get_title = False
        # self.number is always a list of strings, e.g. ['1', '2', '7'] for section
        # 1.2.7
        self.number = ["1"]
        super().start("div", {"class": "index"})
        super().start("ul")

    # What to do in the case of different tags
    def start(self, tag, attrs):
        # Increase page count on <pb/>
        if outline_tag_eq(tag, "pb") and find_attr(attrs, "type") != "pdf":
            self.page += 1
        # Start section on <div xml:id="text-idX.X.X">
        elif outline_tag_eq(tag, "div"):
            for key, value in attrs.items():
                if key.endswith("id"):
                    if value.startswith(self.text):
                        number = value[len(self.text) :].split(".")
                        # Write the previous section.
                        self.write_section()
                        self.in_progress = Section(number, "", str(self.page))
                        break
                    else:
                        logging.warning(f'Found a <div> with the "id" attribute, but the start of its value didn\'t match the current text ID like I expected!\n{self.report_location()}\nValue of "id" attribute: "{value}"\nCurrent text ID: "{self.text}"')
        # Gather up the title of the section from all content inside <head type="outline">
        elif outline_tag_eq(tag, "head") and find_attr(attrs, "type") == "outline":
            # we're inside a head tag with outline type, so start collecting up
            # the title to put in the outline
            self.get_title = True
        # Warn about <choice> tags found inside <head type="outline">
        elif outline_tag_eq(tag, "choice"):
            if self.get_title:
                logging.warning(f'Found a <choice> tag inside a <head> with type="outline"! This may cause strange results in the finished outline!\n{self.report_location()}')

    def end(self, tag):
        if outline_tag_eq(tag, "head"):
            self.get_title = False

    def data(self, data):
        if self.get_title:
            if self.in_progress:
                new_title = self.in_progress.title + data
                self.in_progress = self.in_progress._replace(title=new_title)

    def close(self):
        self.write_section()
        super().end("ul")
        super().end("div")
        return super().close()

    def write_section(self):
        if self.in_progress is not None:
            # Check if any nested lists need to be opened/closed based on the section
            # number.
            how_many_to_close = len(self.number) - len(self.in_progress.number)
            if how_many_to_close > 0:
                for i in range(how_many_to_close):
                    super().end("ul")
            elif how_many_to_close < 0:
                how_many_to_open = -how_many_to_close
                for i in range(
                    len(self.number), len(self.number) + how_many_to_open - 1
                ):
                    super().start("ul")
                    super().start("li")
                    super().data(".".join(self.in_progress.number[i:]))
                    super().end("li")
                # Start all sections except top-level ones collapsed
                if len(self.number) == 1:
                    super().start("ul", {"id": f'section{"_".join(self.number)}', "class": "collapse in"})
                else:
                    super().start("ul", {"id": f'section{"_".join(self.number)}', "class": "collapse", "style": "height: 0px"})


            super().start("li")
            super().start("a", {"href": self.make_url()})
            # Warn if title starts with a section number
            if re.match("\s*([0-9]+\.)*[0-9]+ +.*", self.in_progress.title):
                logging.warning(f'Found a <head> with type="outline" whose content looks like it starts with a section number. Since section numbers are added automatically by the Outline Builder, this might look like a duplicated section number in the finished outline!\n{self.report_location()}\nContent: "{self.in_progress.title}"')
            super().data(
                f'{".".join(self.in_progress.number)} {self.in_progress.title.strip()}'
                # i.e., 1.3.1 Licencia
            )
            super().end("a")

            # Generate a drop-down button for every outline item. We'll delete the ones that dont work later
            target_section = f'section{"_".join(self.in_progress.number)}'
            super().start("button", {"class": "collapsed", "data-toggle": "collapse", "data-target": f'#{target_section}'})
            super().start("div", {"class": "caret"})
            super().end("div")
            super().end("button")

            super().end("li")
            self.number = self.in_progress.number

    def make_url(self):
        return f"/en/texts/{self.text}/{self.in_progress.page}/original"

    def report_location(self):
        page = f'page ~{self.page}'
        if self.in_progress:
            section = f'section {".".join(self.in_progress.number)}'
            return f'Location: {page}, {section}'
        else:
            return f'Location: {page}'



def generate_outline(path, output_path, *, text, preview):
    logging.debug(f"generating{' Preview' if preview else ''} Outline for {text}")
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()

    target = OutlineBuilder(text=text)
    parser = ET.XMLParser(target=target)
    parser.feed(data)
    root = target.close()

    # Delete button elements that don't have a corresponding section
    existing_sections = [ul.attrib['id'] for ul in root.findall('.//ul[@id]')]
    parent_map = {c:p for p in root.iter() for c in p}
    for button in root.findall('.//button'):
        if button.attrib['data-target'][1:] not in existing_sections:
            parent_map[button].remove(button)  # workaround for `button.getparent().remove(button)` using parent_map definition above

    with open(output_path, "w", encoding="utf-8") as f:
        htmlstr = ET.tostring(root, encoding="unicode")
        output = OUTLINE_PREVIEW_TEMPLATE.format(htmlstr) if preview else htmlstr
        f.write(output)


def generate_html(tei_root, *, xslt_path, flex_path, text, spellchoice, abbrchoice):
    logging.debug(f"generating HTML! spellchoice: {spellchoice}")
    xslt_transform = etree.XSLT(etree.parse(xslt_path).getroot())
    # Make sure that all of the keyword arguments are string-encoded, because we're
    # about to pass them to the XSLT stylesheet.
    abbrchoice = etree.XSLT.strparam(abbrchoice)
    spellchoice = etree.XSLT.strparam(spellchoice)
    pseudo_html_root = xslt_transform(
        tei_root, abbrchoice=abbrchoice, spellchoice=spellchoice
    )
    html_root = paginate(pseudo_html_root, text)

    if flex_path:
        logging.debug(f"Flexifying HTML using flex path {flex_path}")
        html_root = flexify(html_root, flex_path)

    return html_root

def preprocess_xml(xml_string):
    # Condense each choice tag onto one line to eliminate whitespace
    # this regex substitution matches choice tags (even across lines),
    # captures the meaningful parts, and reassembles them without whitespace
    regex = r'(<choice>)(?:\s|\n)*(<orig>.*?</orig>)(?:\s|\n)*(<reg type=(?:".*?"|\'.*?\')>.*?</reg>)(?:\s|\n)*(<reg type=(?:".*?"|\'.*?\')>.*?</reg>)?(?:\s|\n)*(</choice>)'
    subst = "\\g<1>\\g<2>\\g<3>\\g<4>\\g<5>"
    xml_no_choice_whitespace = re.sub(regex, subst, xml_string, 0, re.IGNORECASE | re.MULTILINE)
    return xml_no_choice_whitespace

def parse_xml_file(path):
    with open(path, "r", encoding="utf-8") as f:
        xml = f.read()
        xml_cleaned = preprocess_xml(xml)
        return etree.XML(bytes(xml_cleaned, encoding="utf-8"))
