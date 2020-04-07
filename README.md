VtES Deck importer for Tabletop Simulator
========================================

This is a simple deck importer for the table top simulator VtES module.

Note that it is poorly tested and hastily implemented, so bugs are present and you'll have to deal with it.

Requirements
------------

This requires python 3 and a copy of the TTS VtES deck module, which is used to extract the correct card information.

Usage
-----

import.py `<deck file>` `[<TTS asset file>]`

It will save the deck as "Deck.json". Move it to the TTS "Saved objects" folder and rename as desired.

`<deck file>` is the deck to import

If not specified, the import script will try to find the asset file in the expected location, but this is fragile.
If it fails to find the file, specify the full location as the second argument

Input files
------------

The deck format is simplisitc, but should also work for standard ARDB text files.

Note that the card name mapping may not handle accented characters correctly. It uses a rule-based system to
convert names to the identifiers used in the TTS module, but this has been reversed engineered by spot
checking names, and may not work for all cases.

The imput file should look something like

Crypt

2x Name1
4x Name2
....


Library

2x Name3
3x Name4
....


The lines Crypt and Library must appear in the file, otherwise the cards will not be assigned to the correct
decks in the TTS object. Actual card entries must start with a number - either '1x' or '1 '.
The import plugin will try to handle lines like '1x Zoe 3 AUS' correctly, but this parsing is a bit fragile.
In-line comments, as used in the TWDA, are not handled correctly.

