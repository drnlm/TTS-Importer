#!/usr/bin/env python3

import os
import sys
import re
import string
import json
import unicodedata

from typing import Dict, List

NONNAME = re.compile(r'\W')
DIGITS = re.compile(r'\d+$')

DECK_TEMPLATE = os.path.join(os.path.dirname(sys.argv[0]), 'Templates', 'Deck_Template.json')
DECK_THUMBNAIL = os.path.join(os.path.dirname(sys.argv[0]), 'Templates', 'Deck_Template.pmg')


# We handle cases where either the card name has not been updated in the json file, or
# it has and we might have older names
SPECIAL_CASES = {
    'pentexsubversion': 'pentextmsubversion',
    'pentexlovesyou': 'pentextmlovesyou',
    'mylanhorseedgoblin': 'mylanhorseed',
}

def unaccent(sData: str) -> str:
    """Remove unicode accents.

       Convert to normed decomposed for and then strip non-ascii characters"""
    sNormed = unicodedata.normalize('NFD', sData)
    return "".join(b for b in sNormed if ord(b) < 128)


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
            # Normalise unicode characters
            aParts = [unaccent(x) for x in aParts]
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
            if aName[0] == 'the':
                aName = aName[1:] + [aName[0]]
            sName = ''.join(aName)
            if sName in SPECIAL_CASES:
                sName = SPECIAL_CASES[sName]
            if bInCrypt:
                aCrypt.extend([sName]*iNum)
            else:
                aLibrary.extend([sName]*iNum)
    return [aCrypt, aLibrary]


def create_json(aData: List[List[str]], dTTSJson: Dict[str, Dict]) -> None:
    """Create the TTS Json file"""
    # Load Template
    with open(DECK_TEMPLATE, 'r') as oF:
        dDeckBase = json.load(oF)
    dCryptTransform = dDeckBase['ObjectStates'][0]['ContainedObjects'][0]['Transform'].copy()
    dLibraryTransform = dDeckBase['ObjectStates'][1]['ContainedObjects'][0]['Transform'].copy()

    dThisDeck = dDeckBase.copy()
    dCrypt = dThisDeck['ObjectStates'][0]
    dLibrary = dThisDeck['ObjectStates'][1]
    dCrypt['ContainedObjects'] = []
    dCrypt['DeckIDs'] = []
    dCrypt['CustomDeck'] = {}


    dLibrary['ContainedObjects'] = []
    dLibrary['DeckIDs'] = []
    dLibrary['CustomDeck'] = {}
    # Create crypt
    for sName in aData[0]:
        if sName not in dTTSJson:
            raise RuntimeError(f"Missing object for {sName}")
        oObj = dTTSJson[sName]
        oCard = oObj.copy()
        # This doesn't seem to matter much, but it gets set, so we do likewise
        oCard['Transform'] = dCryptTransform
        dCrypt['DeckIDs'].append(oCard['CardID'])
        dCrypt['CustomDeck'].update(oCard['CustomDeck'])
        dCrypt['ContainedObjects'].append(oCard)

    # Create library
    for sName in aData[1]:
        if sName not in dTTSJson:
            raise RuntimeError(f"Missing object for {sName}")
        oObj = dTTSJson[sName]
        oCard = oObj.copy()
        oCard['Transform'] = dLibraryTransform
        dLibrary['DeckIDs'].append(oCard['CardID'])
        dLibrary['CustomDeck'].update(oCard['CustomDeck'])
        dLibrary['ContainedObjects'].append(oCard)

    with open('Deck.json', 'w') as oF:
        json.dump(dThisDeck, oF)


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


def gen_prefixes(dTTSJson: Dict[str, Dict]) -> None:
    """ARDB's text format truncates vampire names to 18 characters, so
       we generate prefixes for the names referencing the same objects.
       Since we're doing it from the nicknames, and don't know how many
       spaces where replaced, this is rather hack'ish and inefficient"""
    # We're mutating the dictionary, so we need to iterate over the keys
    for sName in list(dTTSJson.keys()):
        if len(sName) < 13:
            # Too short to worry about
            continue
        for iLength in (12, 13, 14, 15, 16, 17, 18):
            sPrefix = sName[:iLength]
            if sPrefix not in dTTSJson:
                dTTSJson[sPrefix] = dTTSJson[sName]


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
    gen_prefixes(dTTSData)
    aDeckData = parse_file(sys.argv[1])
    create_json(aDeckData, dTTSData)



