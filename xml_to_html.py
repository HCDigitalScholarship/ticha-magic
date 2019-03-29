"""
Turn XML into HTML (by way of an intermediate pseudo-HTML step).

The main module functions are convert_tei_to_html() and paginate().
"""
from lxml import etree, sax

from common import tag_eq


def convert_tei_to_html(xml_root, xslt_file, textname='', **kwargs):
    """
    Apply the XSLT stylesheet to the TEI-encoded XML document, but do not paginate.
    """
    xslt_transform = etree.XSLT(etree.parse(xslt_file).getroot())
    # Make sure that all of the keyword arguments are string-encoded, because we're
    # about to pass them to the XSLT stylesheet.
    for key, val in kwargs.items():
        if isinstance(val, str):
            kwargs[key] = etree.XSLT.strparam(val)
    return xslt_transform(xml_root, **kwargs)


def paginate(pseudo_html_root, text_name):
    """
    Paginate the output of convert_tei_to_html. This entails removing all <pb/> elements
    and adding <div class="page">...</div> elements to wrap each page. The output of
    this function is valid HTML.
    """
    handler = TEIPager(text_name)
    sax.saxify(pseudo_html_root, handler)
    return handler.etree


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
            msg = 'Tried to close <{}>'.format(qname)
            if self.real_tag_stack:
                msg += ', but last opened tag was <{}>'.format(self.real_tag_stack[-1])
            else:
                msg += ', but no tags have been opened'
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
        if tag_eq(qname, 'pb'):
            if attributes.get((None, 'type')) != 'pdf':
                recto_verso_no = attributes.get((None, 'n'), '')
                self.handlePageBreak(recto_verso_no)
        elif tag_eq(qname, 'cb'):
            n = attributes.get((None, 'n'))
            self.handleColumnBreak(n)
        elif tag_eq(qname, 'body'):
            self.startElement('div')
            self.startNewPageDiv(str(self.page), '0')
        else:
            if tag_eq(qname, 'br'):
                self.line += 1
            self.tag_stack.append( (ns_name, qname, attributes) )
            super().startElementNS(ns_name, qname, attributes)

    def handlePageBreak(self, recto_verso_no):
        self.line = 1
        self.page += 1
        self.closeAllTags()
        self.endElement('div')
        self.startNewPageDiv(str(self.page), recto_verso_no)
        self.reopenAllTags()

    def startNewPageDiv(self, page_no, recto_verso_no):
        attrs = {
            'class': 'printed-text-page ' + self.text_name,
            'data-n': page_no,
            'data-rvn': recto_verso_no,
        }
        self.startElement('div', attrs)

    def handleColumnBreak(self, n):
        if n == '1':
            # A value of '1' indicates start of column section.
            self.startElement('div')
            self.startElement('div', {'class': 'col-xs-6'})
        elif n == '':
            # An empty value indicates end of column section.
            self.endElement('div')
            self.endElement('div')
        else:
            self.endElement('div')
            self.startElement('div', {'class': 'col-xs-6'})

    def endElementNS(self, ns_name, qname):
        # Ignore self-closing <pb> and <cb> tags; they were already handled by
        # startElementNS.
        if tag_eq(qname, 'body'):
            self.endElement('div')
            self.endElement('div')
        elif not tag_eq(qname, 'pb') and not tag_eq(qname, 'cb'):
            closes = self.tag_stack.pop()
            try:
                super().endElementNS(ns_name, qname)
            except sax.SaxError as e:
                raise sax.SaxError(
                    str(e) + 'on page {0.page}, line {0.line}'.format(self)
                ) from e

    def closeAllTags(self):
        for ns_name, qname, _ in reversed(self.tag_stack):
            super().endElementNS(ns_name, qname)

    def reopenAllTags(self):
        for ns_name, qname, attributes in self.tag_stack:
            super().startElementNS(ns_name, qname, attributes)
