Tools for manipulating TEI-encoded documents on the [Ticha](https://ticha.haverford.edu) project.

The `ticha_magic` library can
  - Convert a TEI-encoded XML file into HTML.
  - Make an HTML outline out of a TEI document.
  - Insert linguistic annotations from [FLEx](https://software.sil.org/fieldworks/) into an HTML
    document.

**Please note**: The scripts in this repository have only been tested against the TEI documents
produced by the Ticha project at Haverford, and will likely not work as expected or at all for
other TEI documents.


## Workflow
To convert an XML document to HTML:

```bash
$ ./ticha_magic cordova_arte.xml # output in cordova_arte.html
```

To specify a specific output file (otherwise, the output file is inferred from the name of the input
file):

```bash
$ ./ticha_magic cordova_arte.xml -o output.html
```

To insert FLEx annotations after HTML conversion:

```bash
$ ./flexml_to_json.py flex_export_from_brook.xml # create the JSON file
$ ./ticha_magic cordova_arte.xml -f flex_export_from_brook.json
```

To specify a custom XSLT file (otherwise, the proper XSLT file is inferred from the name of the
input file, defaulting to `xslt/base.xslt`):

```bash
$ ./ticha_magic cordova_arte.xml -x xslt/custom_arte.xslt
```

To see more options, run `./ticha_magic --help`.

You can also instantly preview a text like this:

```bash
$ ./preview cordova_arte.xml
```

The `preview` script should open up the HTML document in your default web browser, with mostly the
same CSS and page layout as on the actual Ticha site. The script takes all the same arguments as
`ticha_magic`, except you shouldn't pass it `-o` because it sets its own output file.


## TEI to HTML conversion
Converting a TEI-encoded XML document into HTML that we can display on Ticha entails doing the
following:

- Converting TEI tags like `<lb/>` into HTML tags like `<br>`.
- Choosing what text to include. Some of our TEI documents, like Cordova's Arte, have `<choice>`
  tags that encode both the original spelling in the document, and a rendition in regularized
  Spanish. There is also a choice between using the full spelling and abbreviations.
- Paginating the TEI document. Page breaks are indicated in TEI by the `<pb/>` tag; these need to
  be converted into HTML `<div class="page">...</div>` elements that wrap each page. A similar
  transformation must be done for columns indicated by the `<cb/>` tag.
- Inserting FLEx annotations. Brook has annotated a large number of the Zapotec words in Cordova's
  Arte and provided us with an XML export of her annotations. Each annotation needs to be matched
  with its corresponding word in the HTML, and the contents of the annotation has to be inserted.
  Since there are multiple occurrences of the same word in different parts of the text with
  different annotations, this is a non-trivial process.

The first two bullet points are handled by our [XSLT](https://en.wikipedia.org/wiki/XSLT)
stylesheets in the `xslt` folder.

The last two bullet points are handled by the Python code in `ticha_magic.py`. Pagination and FLEx
insertion are done with SAX parsers because they have to do tree insertions that are difficult to
accomplish with DOM parsers. The details of their implementations are documented in the source code.

## TEI to outline
Making an outline from a TEI document is straightforward compared to converting it to HTML. See
the `make_outline.py` script for details.
