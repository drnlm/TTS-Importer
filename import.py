#!/usr/bin/env python3

import os
import sys

def parse_file(sFileName):
    """Parse a ARBD'ish text file and return a list of crypt identifiers
       and a list library identifiers"""


def create_json(aData, dTTSJson):
    """Create the TTS Json file"""


def load_tts_json(sFileName):
    """Load the json file specifying the card objects"""


def find_json_file():
    """Try to find the VtES TTS module file"""
    DEFAULT = "1955001917.json"
    if sys.platform.startswith("win") and "APPDATA" in os.environ:
        sCand = os.path.join(os.environ["APPDATA"], "Tabletop Simulator", "Mods", "Workshop", DEFAULT)
    else:
        sCand = os.path.join(os.path.expanduser("~"), ".local", "share", "Tabletop Simulator", "Mods", "Workshop", DEFAULT)
    if os.path.exists(sCand):
        return sCand
    raise RuntimeError(f"Failed to find TTS Json module: {DEFAULT}. Please specify it's location")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        sJsonFile = sys.argv[2]
    else:
        sJsonFile = find_json_file()
    print(f"Using {sJsonFile} for TTS data")
    dTTSData = load_tts_json(sJsonFile)
    aDeckData = parse_file(sys.argv[1])
    create_json(aDeckData, dTTSData)



