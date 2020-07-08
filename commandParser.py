#!/usr/bin/python3
class Parser():
    '''Parses commands into command type and arguments'''
    def __init__(self, fileURI):
        self.fileURI = fileURI
        self.commands = self.getCommands(fileURI)
    
    def clean(self, line):
        'Removes line comments and leading and trailling whitespace from command'
        return line.partition("//")[0].strip()

    def getCommands(self, fileURI):
        'Creates generator for processed commands'
        with open(fileURI, 'r') as vmFile:
            while True:
                line = vmFile.readline()
                if not line:
                    break
                if self.clean(line):
                    yield self.process(self.clean(line))

    def process(self, line):
        '''Parses clean (no comments, no leading or trailling whitespace)
        commands into command dicts'''
        parts = line.split()
        return {"command": line,
                "commandType": self.commandTypes(parts[0]),
                "args": parts[1:]}

    def commandTypes(self, command):
        arithmetic = set(("add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"))
        types = {
            "push" : "C_PUSH",
            "pop" : "C_POP",
            "label" : "C_LABEL",
            "goto" : "C_GOTO",
            "if-goto" : "C_IF",
            "function" : "C_FUNCTION",
            "return" : "C_RETURN",
            "call" : "C_CALL"
        }
        if command in arithmetic:
            return "C_ARITHMETIC"
        else:
            return types[command]
