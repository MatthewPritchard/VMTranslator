#!/usr/bin/python3
from sys import argv
import os
from commandParser import Parser
from commandWriter import Writer
if __name__ == "__main__":
    path = os.path.abspath(argv[1])
    isDir = False
    if os.path.isdir(path):
        parsers = [Parser(os.path.join(path, filename)) for filename in os.listdir(path) if filename.endswith(".vm")]
        outURI = os.path.join(path, os.path.basename(path) + ".asm")
        isDir = True
    elif os.path.isfile(path):
        parsers = [Parser(argv[1])]
        outURI = path.partition(".vm")[0] + ".asm"
    else:
        raise IOError("not a file or directory")
    
    writer = Writer(outURI, isDir)
    
    for parser in parsers:
        writer.setFilename(parser.fileURI)
        for line in parser.commands:
            writer.write(line)
