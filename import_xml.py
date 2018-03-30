from django.core.exceptions import MultipleObjectsReturned

from . import ticha_magic, make_outline
from ticha.settings import BASE_DIR

import contextlib
import os.path
from lxml import etree, sax


import logging
logger = logging.getLogger('ticha')


class ImportXMLError(Exception):
    pass


def import_xml(doc, xml_data, flex_data):
    """Convert the XML data to HTML, generate an outline in ticha/templates/ticha, and save each
    page as a Page object.
    """
    # Make the HTML outline for the document.
    try:
        doc.outline = outline_html = make_outline.xml_to_outline(xml_data, doc.slug)
    except:
        pass
    # Parse the XML into an XML tree.
    try:
        xml_root = etree.XML(xml_data)
    except etree.XMLSyntaxError as e:
        raise ImportXMLError(str(e)) from None
    # Convert the XML to HTML and insert FLEx annotations.
    xml_kwargs = {'spellchoice': 'orig', 'abbrchoice': 'abbr', 'textname': doc.title.lower()}
    try:
        orig_tree = ticha_magic.xml_to_html(xml_root, doc.slug, flex_data=flex_data, **xml_kwargs)
    except sax.SaxError as e:
        raise ImportXMLError(str(e)) from None
    xml_kwargs['spellchoice'] = 'reg-spanish'
    try:
        reg_tree = ticha_magic.xml_to_html(xml_root, doc.slug, **xml_kwargs)
    except sax.SaxError as e:
        raise ImportXMLError(str(e)) from None
    # Paginate the HTML document and add each page to the database.
    for i, (orig_elem, reg_elem) in enumerate(zip(orig_tree.getroot(), reg_tree.getroot())):
        with contextlib.suppress(MultipleObjectsReturned):
            page, _ = doc.page_set.get_or_create(man=doc, linear_page_number=i)
            page.transcription = etree.tostring(orig_elem, encoding='unicode', method='html')
            page.transcription_regular = etree.tostring(reg_elem, encoding='unicode', method='html')
            page.page_id = orig_elem.attrib.get('data-rvn', '')
            page.save()
    doc.last_page = i
    doc.save()
    logger.debug('Successfully uploaded XML transcription for %s', doc.title)
