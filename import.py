#!/usr/bin/env python3

import os
import sys
import re
import string

import json

from typing import Dict, List

NONNAME = re.compile(r'\W')
DIGITS = re.compile(r'\d+$')

def parse_file(sFileName: str) -> List[List[str]]:
    """Parse a ARBD'ish text file and return a list of crypt identifiers
       and a list library identifiers"""
    aCrypt: List[str] = [] 
    aLibrary: List[str] = []
    bInCrypt = False
    bInLibrary = False
    with open(sFileName, 'r') as oFile:
        for sLine in oFile.readlines():
            sLine = sLine.strip().lower()
            if not sLine:
                continue
            if sLine.startswith('crypt') and not bInCrypt:
                bInCrypt = True
                bInLibrary = False
                continue
            if sLine.startswith('library') and not bInLibrary:
                bInCrypt = False
                bInLibrary = True
                continue
            if not (bInLibrary or bInCrypt):
                continue
            if not sLine[0] in string.digits:
                continue
            sDigit, sRest = sLine.split(' ', 1)
            if sDigit.endswith('x'):
                sDigit = sDigit[:-1]
            iNum = int(sDigit)
            aParts = sRest.split()
            aName = [NONNAME.sub('', aParts[0])]  # Mainly to handle 44 magnum and 419 operation
            for sCand in aParts[1:]:
                # We add bits until we reach something that looks like a capacity number, or the end of the string
                if len(sCand) < 3:
                    # Only consider one or two digit numbers
                    if DIGITS.match(sCand):
                        break
                sCand = NONNAME.sub('', sCand)
                aName.append(sCand)
            # Already lowercase
            sName = ''.join(aName)
            if bInCrypt:
                aCrypt.extend([sName]*iNum)
            else:
                aLibrary.extend([sName]*iNum)
    return [aCrypt, aLibrary]


def create_json(aData: List[List[str]], dTTSJson: Dict[str, Dict]) -> None:
    """Create the TTS Json file"""
    # Create crypt
    for sName in aData[0]:
        if sName not in dTTSJson:
            raise RuntimeError(f"Missing object for {sName}")

    # Create library
    for sName in aData[1]:
        if sName not in dTTSJson:
            raise RuntimeError(f"Missing object for {sName}")



def load_tts_json(sFileName: str) -> Dict[str, Dict]:
    """Load the json file specifying the card objects"""
    dRes: Dict[str, Dict] = {}
    with open(sFileName, 'r') as oF:
        dData = json.load(oF)
        # We want to extract the 2 relevant chunks as a set
        # of 'name: object' entries
        # This is potentially unstable when the module is updated
        # Crypt Deck
        for oObj in dData['ObjectStates'][0]['ContainedObjects']:
            dRes[oObj['Nickname']] = oObj
        # And Library Deck
        for oObj in dData['ObjectStates'][1]['ContainedObjects']:
            dRes[oObj['Nickname']] = oObj
    return dRes



def find_json_file() -> str:
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



