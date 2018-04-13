"""
The new architecture of the FLEx inserter:

    1. Convert the FLEx XML export into a stripped-down JSON file that includes only the information
       that is needed for insertion (which is just the word, the section it appears in, and the
       HTML text of the popover element to be inserted).
    2. Load the JSON file into a Python dictionary and insert FLEx annotations into the text as
       before.

Should the JSON file be persistent, or created every time?

  Probably better for it to be persistent since creating it will be probably be an expensive
  operation.

What should the interface be?

    1. The user supplies only the XML export, and the script creates the JSON file.
    2. The user supplies either the XML export or the JSON file, and the script just does the right
       thing.
    3. The user supplies only the JSON file; a separate script exists to convert the XML to JSON.
"""
