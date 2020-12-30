#!/usr/bin/env python3
import os
from pathlib import Path
import sys

__projectdir__ = Path(os.path.dirname(os.path.realpath(__file__)) + '/')

import re 

# Definitions:{{{1
# note that at start I allow for either the start of a line or a new line (^ doesn't work, perhaps due to using DOTALL)
bibfilerefpattern = re.compile(r"(?:^|\n)@[a-z]*?{([a-z0-9-]*?),\n(.*?)\n}", re.DOTALL)

# Auxilliary Functions:{{{1
def getfilenames(name):
    import os

    with open(__projectdir__ / Path('refs/searchfolders.txt'), 'r') as f:
        searchfolders = f.read().splitlines()

    retfilenames = []

    for searchfolder in searchfolders:
        for root, dirs, files in os.walk(searchfolder):
            for filename in files:
                if filename.split('.')[0] == name:
                    retfilenames.append(os.path.join(root, filename))

    return(retfilenames)


# Open Citation:{{{1
def openfilename(name, pagenumber = None):
    import re
    import subprocess
    import sys

    retfilenames = getfilenames(name)

    if len(retfilenames) != 1:
        print('Number of filenames with this pattern incorrect: ' + str(retfilenames))
        sys.exit(1)
    else:
        retfilename = retfilenames[0]
    
    if pagenumber is None:
        openpagenumber = None
    else:
        # get base page numbers i.e. number of pages before numbered pages begin
        with open(__projectdir__ / Path('refs/pagenumbers.txt'), 'r') as f:
            pagenumbers = f.read().splitlines()
            pagenumbers = [line for line in pagenumbers if not line.startswith('#')]
            pagenumbers = [line.split(',') for line in pagenumbers]
        
        basepagenumber = None
        for line in pagenumbers:
            if line[0] == name:
                basepagenumber = int(line[1])
        
        # if not found, try going to bibfilename
        if basepagenumber is None:
            with open(__projectdir__ / Path('refs/bibfile.txt'), 'r') as f:
                bibfile = f.read()
            if bibfile[-1] == '\n':
                bibfile = bibfile[: -1]
            with open(bibfile) as f:
                text = f.read()
                
            matches = bibfilerefpattern.finditer(text)
            for match in matches:
                if match.group(1) == name:
                    if basepagenumber is None:
                        bibfileref = match.group(0)
                        pagepattern = re.compile('pages *?= *?[{"]([0-9]*)')
                        match2 = pagepattern.search(bibfileref)
                        if match2:
                            # if pages = 2-10 then and have \cite[p.2] then want to open pdf at page 1
                            # so basepagenumber = -2 + 1
                            basepagenumber = -int(match2.group(1)) + 1
                    else:
                        raise ValueError('Multiple matches have this name.')

        if basepagenumber is None:
            basepagenumber = 0

        openpagenumber = pagenumber + basepagenumber

    if retfilename.endswith('.pdf'):
        if openpagenumber is None:
            subprocess.check_output([__projectdir__ / Path('pdf.sh'), retfilename])
        else:
            subprocess.check_output([__projectdir__ / Path('pdf.sh'), '--page', str(openpagenumber), retfilename])
    elif retfilename.endswith('.html'):
        subprocess.call(['google-chrome', retfilename])
    else:
        None


def opencitation(filename, pos, externalaltlabelsfiles = []):
    import re
    import sys

    # toparse = sys.argv[1]
    # toparsesplit = toparse.split('SPLITSTRHERE')
    # filename = toparsesplit[0]
    # pos = int(toparsesplit[1])

    with open(filename, 'r', encoding = 'latin-1') as f:
        text = f.read()

    # try matching \cite{}:
    citepattern = re.compile(r'\\[a-z]*cite[a-z]*(\[.*?\]|){(.*?)}')
    matches = citepattern.finditer(text)
    
    thematch = None
    for match in matches:
        if pos > match.start() and pos < (match.end() + 2):
            thematch = match
            break

    # if am using external altlabels
    if externalaltlabelsfiles != [] and thematch is None:
        externalaltlabelsdict = {}
        for filename in externalaltlabelsfiles:
            with open(filename) as f:
                lines = f.read().split('\n')
            lines = [line for line in lines if not line.startswith('#')]
            lines = [line for line in lines if line != '']
            for line in lines:
                externalaltlabelsdict[line.split(';')[0]] = line.split(';')[1]
        matches = re.compile(r'\\(altlabel|altref|altinput){(.*?)}').finditer(text)

        for match in matches:
            if pos > match.start() and pos < (match.end() + 2):
                if match.group(2) in externalaltlabelsdict:
                    thematch = citepattern.search(externalaltlabelsdict[match.group(2)])
                    # don't need to check pos since know pos correct
                break

    if thematch is None:
        print('ERROR: No match at cursor ')
        return('No matches')

    pagenumber = None
    if thematch.group(1) != '':
        pagenumbermatch = re.compile('\[pp?\.([0-9]*).*\]').search(thematch.group(1))
        if pagenumbermatch:
            pagenumber = int(pagenumbermatch.group(1))

    openfilename(thematch.group(2), pagenumber = pagenumber)

    
def opencitation_ap():
    #Argparse:{{{
    import argparse
    
    parser=argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("pos", type = int)
    parser.add_argument("--externalaltlabelsfiles", nargs = '+')
    
    args=parser.parse_args()

    opencitation(args.filename, args.pos, externalaltlabelsfiles = args.externalaltlabelsfiles)
    #End argparse:}}}


# Save links to all citation names:{{{1
def citationnamefolderlinks(bibnames, linkfolder):
    """
    If you save all the different citation items in a directory structure, i.e. macro/book1, micro/book2 etc. it might be nice to have a folder in which you save all the citations without this structure.
    So this function saves links to the files called in bibnames in linkfolder.
    """

    if not isinstance(bibnames, list):
        bibnames = [bibnames]

    # make folder if not exist
    if not os.path.isdir(linkfolder):
        os.mkdir(linkfolder)

    # remove links
    for link in os.listdir(linkfolder):
        os.remove(os.path.join(linkfolder, link))

    citationnames = []
    for bibname in bibnames:
        with open(bibname) as f:
            text = f.read()

        for match in bibfilerefpattern.finditer(text):
            citationnames.append(match.group(1))

    for citationname in citationnames:
        filenames = getfilenames(citationname)

        if len(filenames) >= 2:
            print('ERROR: Multiple matches for citation. Citation: ' + citationname + '. Matches: ' + ', '.join(filenames))

        if len(filenames) == 1:
            os.symlink(filenames[0], os.path.join(linkfolder, os.path.basename(filenames[0])))


