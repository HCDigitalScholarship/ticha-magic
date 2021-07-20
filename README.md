# ticha-magic

Tools for manipulating TEI-encoded documents on the [Ticha](https://ticha.haverford.edu) project.

## Background

The `ticha-magic` library can
  - Convert a TEI-encoded XML file into HTML.
  - Make an HTML outline out of a TEI document.
  - Insert linguistic annotations from [FLEx](https://software.sil.org/fieldworks/) into an HTML document.

**Please note:** The scripts in this repository have only been tested against the TEI documents produced by the Ticha project at Haverford, and will likely not work as expected or at all for other TEI documents.

## Installing

To install `ticha-magic` on your machine:

1. Clone this repo: `git clone https://github.com/HCDigitalScholarship/ticha-magic.git`
2. Go into the project directory: `cd ticha-magic`
3. Install dependencies:
  * [lxml](https://lxml.de/)
    * `conda install -c anaconda lxml` to install with [Anaconda](https://anaconda.org/anaconda/lxml)
    * **OR**
    * `pip install lxml` to install with [pip](https://pypi.org/project/lxml/)

### Dependencies

* [Python 3](https://www.python.org/)
* [lxml](https://lxml.de/)

## Use

### The CLI

```
usage: tei_to_html.py [-h] -t {levanto-arte,levanto-catechismo,cordova-arte} [-d] infile

Convert a TEI-encoded text to HTML.

positional arguments:
  infile                path to a TEI file to convert

optional arguments:
  -h, --help            show this help message and exit
  -t, --text {levanto-arte,levanto-catechismo,cordova-arte}
                        text ID indicating what formatting to use when converting
  -d, --debug           print debugging output
```

### Convert a TEI-encoded XML file into HTML and make an HTML outline

For a file `example.xml`, one of the commands

```shell
$ ./tei_to_html.py example.xml -t cordova-arte
$ ./tei_to_html.py example.xml -t levanto-arte
$ ./tei_to_html.py example.xml -t levanto-catechismo
```

generates:
* An HTML outline
* An original HTML file
  * (Plus a preview file for the above)
* A regularized HTML file
  * (Plus a preview file for the above)

(Preview files open nicely in a browser and make it convenient to check that the output was what you expected.)

*FIXME: Since each document is different, the `-t` option takes an argument specifying the document being converted. Newly encoded documents require a modification to ticha-magic before they can be converted.*

### Insert linguistic annotations from FLEx into an HTML document.

*FIXME*


## Workflow

To publish an updated TEI-encoded document to Ticha:

0. (Before publishing, it's a good idea to go look at the Ticha webpages for the document you're updating so you can compare later and see if you broke something.)


1. Use Atom's linter to check that there are no errors in your XML. [Instructions in the `ticha-xml-tei` repo](https://github.com/HCDigitalScholarship/ticha-xml-tei#linting).
2. Navigate to the `ticha-magic` project directory
3. Run `./tei_to_html.py path/to/your/file.xml -t document-name` (following CLI documentation above) to generate HTML from your XML file.
4. In the Ticha admin interface, click "Import an HTML transcription" under "COMMON TASKS".
5. Select the document you're updating from the drop-down.
6. Use the three file selectors to upload the `text-id.html`, `text-id_reg.html`, and `text-id_outline.html` files you generated in their respective spots.
7. Click "Submit"! If there are errors in the file, a red banner will appear. If everything went well, a green banner will appear.
8. Go check the text and outline pages to make sure everything worked. If it did, admire your handiwork! If it didn't, get in touch with Mike.


## Developing

This section discussed the technical details for people who want to tinker with the code.

### TEI to HTML conversion

Converting a TEI-encoded XML document into HTML that we can display on Ticha entails doing the following:

- **Preprocessing the XML document.** When doing encoding in XML, using indentation is helpful for human encoders, but indentation is not ignored in XML. Regex preprocessing is done on the XML before it's parsed to remove whitespace within `<choice>` tags, which prevents this whitespace from "leaking" into the final HTML output.
- **Converting TEI tags into HTML tags.** For example, `<lb/>` in TEI becomes `<br>` in HTML.
- **Choosing what text to include.** Some of our TEI documents, like Cordova's Arte, have `<choice>` tags that encode both the original spelling in the document, and a rendition in regularized Spanish. There is also a choice between using the full spelling and abbreviations.
- **Paginating the TEI document.** Page breaks are indicated in TEI by the `<pb/>` tag; these need to be converted into HTML `<div class="page">...</div>` elements that wrap each page. A similar transformation must be done for columns indicated by the `<cb/>` tag.
- **Inserting FLEx annotations.** Brook has annotated a large number of the Zapotec words in Cordova's Arte and provided us with an XML export of her annotations. Each annotation needs to be matched with its corresponding word in the HTML, and the contents of the annotation has to be inserted.  Since there are multiple occurrences of the same word in different parts of the text with different annotations, this is a non-trivial process.

The first two bullet points are handled by our [XSLT](https://en.wikipedia.org/wiki/XSLT) stylesheets in the [`xslt` folder](xslt/).

Pagination and FLEx insertion are done with SAX parsers because they have to do tree insertions that are difficult to accomplish with DOM parsers. The details of their implementations are documented in the source code.

### Tests

To run tests, from the root project directory, run

```shell
python3 test.py
```

The expected HTML outputs of the conversion are in the `tests` subdirectory. The test script runs conversion on `input.xml` and compares to these expected outputs. If you change the way something works, update tests to pass.
