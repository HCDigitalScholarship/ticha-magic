import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a TEI-encoded text to HTML.")
    parser.add_argument("infile", help="Path to TEI file to convert")
    parser.add_argument("-o", help="Prefix for output files")
    parser.add_argument("--xslt", help="Path to XSLT stylesheet")
    parser.add_argument("--flex", help="Path to FLEx export (either XML or JSON)")
    parser.add_argument(
        "--spellchoice", default="orig", choices=["orig", "reg-spanish", "reg-spacing"]
    )
    parser.add_argument("--abbrchoice", default="abbr", choices=["abbr", "expan"])
    args = parser.parse_args()

    print("Not implemented yet!")
