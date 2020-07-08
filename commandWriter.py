#!/usr/bin/python3
import os
from collections import Counter


class Writer():
    '''Writes translated commands to a given output file'''
    stacks = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, fileURI, isDir):
        self.file = open(fileURI, "w+")
        self.arithmeticCount = 0
        self.functionCalls = Counter()
        self.handlers = {
            "C_PUSH": self.c_push,
            "C_POP": self.c_pop,
            "C_LABEL": self.c_label,
            "C_GOTO": self.c_goto,
            "C_IF": self.c_if,
            "C_FUNCTION": self.c_function,
            "C_RETURN": self.c_return,
            "C_CALL": self.c_call,
            "C_ARITHMETIC": self.c_arithmetic
        }
        if isDir:
            self.writeInit()
            self.write({"commandType": "C_CALL",
                        "command": "call Sys.init 0",
                        "args": ["Sys.init", "0"]})

    def writeInit(self):
        self.file.write(("@256 // init\n"
                         "D=A\n"
                         "@SP // SP = 256\n"
                         "M=D\n"
                         "D=-1\n"
                         "@LCL // LCL = -1\n"
                         "M=D\n"
                         "D=D-1\n"
                         "@ARG // ARG = -2\n"
                         "M=D\n"
                         "D=D-1\n"
                         "@THIS // THIS = -3\n"
                         "M=D\n"
                         "D=D-1\n"
                         "@THAT // THAT = -4\n"
                         "M=D\n"
                         "D=D-1\n"))

    def setFilename(self, fileURI):
        self.filename = os.path.basename(fileURI).partition(".vm")[0]

    def write(self, command):
        self.file.write(self.handlers[command["commandType"]](command))

    def c_push(self, command):
        original = command["command"]
        args = command["args"]
        if args[0] == "constant":
            constant = args[1]
            return (f"@{constant} // {original}\n"
                    "D=A\n"
                    "@SP\n"
                    "A=M\n"
                    "M=D\n"
                    "@SP\n"
                    "M=M+1\n")
        elif args[0] in self.stacks:
            index = args[1]
            stack = self.stacks[args[0]]
            return (f"@{index} // {original}\n"
                    "D=A\n"
                    f"@{stack}\n"
                    "A=D+M\n"
                    "D=M\n"
                    "@SP\n"
                    "A=M\n"
                    "M=D\n"
                    "@SP\n"
                    "M=M+1\n")
        elif args[0] == "static":
            index = args[1]
            output = (f"@{self.filename}.{index} // {original}\n"
                      "D=M\n"
                      "@SP\n"
                      "A=M\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M+1\n")
            return output
        elif args[0] == "pointer":
            location = "THIS" if not int(args[1]) else "THAT"
            output = (f"@{location} // {original}\n"
                      "D=M\n"
                      "@SP\n"
                      "A=M\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M+1\n")
            return output
        elif args[0] == "temp":
            index = 5+int(args[1])
            output = (f"@{index} // {original}\n"
                      "D=M\n"
                      "@SP\n"
                      "A=M\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M+1\n")
            return output

    def c_arithmetic(self, command):
        unary = {
            "neg": "-",
            "not": "!"
        }
        binary = {
            "add": "+",
            "sub": "-",
            "and": "&",
            "or": "|"
        }
        boolean = {
            "eq": "JEQ",
            "lt": "JLT",
            "gt": "JGT"
        }
        if command["command"] in unary:  # unary operators
            operator = unary[command["command"]]
            original = command["command"]
            output = (f"@SP // {original}\n"
                      "A=M-1\n"
                      f"M={operator}M\n")
            return output
        elif command["command"] in binary:  # binary operators
            operator = binary[command["command"]]
            original = command["command"]
            output = (f"@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "A=A-1\n"
                      f"M=M{operator}D\n")
            return output
        elif command["command"] in boolean:
            operation = boolean[command["command"]]
            count = self.arithmeticCount
            original = command["command"]
            output = (f"@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "A=A-1\n"
                      "D=M-D\n"
                      f"@SKIP.{count}\n"
                      f"D;{operation}\n"
                      "@SP\n"
                      "A=M-1\n"
                      "M=0\n"
                      f"@END.{count}\n"
                      "0;JMP\n"
                      f"(SKIP.{count})\n"
                      "@SP\n"
                      "A=M-1\n"
                      "M=-1\n"
                      f"(END.{count})\n")

            self.arithmeticCount += 1
            return output
        else:
            raise Exception(
                "Arithmetic command not recognised " + command["command"])

    def c_pop(self, command):
        stack = command["args"][0]
        index = command["args"][1]
        original = command["command"]
        if stack in self.stacks:
            stack = self.stacks[stack]
            output = (f"@{index} // {original}\n"
                      "D=A\n"
                      f"@{stack}\n"
                      "D=D+M\n"
                      "@R13\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "@R13\n"
                      "A=M\n"
                      "M=D\n")

        elif stack == "static":
            output = (f"@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      f"@{self.filename}.{index}\n"
                      "M=D\n")

        elif stack == "pointer":
            if index == "0":
                stack = "THIS"
            elif index == "1":
                stack = "THAT"
            else:
                raise Exception(
                    f'pointer index must be 0 or 1: "{command["command"]}"')
            output = (f"@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      f"@{stack}\n"
                      "M=D\n")

        elif stack == "temp":
            stack = int(index)+5
            output = (f"@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      f"@{stack}\n"
                      "M=D\n")

        else:
            raise Exception(f'Invalid pop location: "{command["command"]}"')
        return output

    def c_label(self, command):
        label = command["args"][0]
        original = command["command"]
        return f"({label}) //{original}\n"

    def c_goto(self, command):
        label = command["args"][0]
        original = command["command"]
        return (f"@{label} // {original}\n"
                "0;JMP\n")

    def c_if(self, command):
        label = command["args"][0]
        original = command["command"]
        return (f"@SP // {original}\n"
                "M=M-1\n"
                "A=M\n"
                "D=M\n"
                f"@{label}\n"
                "D;JNE\n")

    def c_function(self, command):
        functionName = command["args"][0]
        original = command["command"]
        output = f"({functionName}) // {original}\n"
        nVars = ("@SP\n"
                 "M=M+1\n"
                 "A=M-1\n"
                 "M=0\n") * int(command["args"][1])
        return output + nVars

    def c_return(self, command):
        original = command["command"]
        output = (f"@LCL // {original}\n"
                  "D=M\n"
                  "@14 // temp variable endFrame\n"
                  "M=D\n"
                  "@5\n"
                  "D=A\n"
                  "@14\n"
                  "A=M-D // LCL-5\n"
                  "D=M\n"
                  "@15 // temp variable retAddr\n"
                  "M=D\n"
                  "@SP // *ARG = POP()\n"
                  "M=M-1\n"
                  "A=M\n"
                  "D=M\n"
                  "@ARG\n"
                  "A=M\n"
                  "M=D\n"
                  "@ARG // SP=ARG+1\n"
                  "D=M+1\n"
                  "@SP\n"
                  "M=D\n"
                  "@14 // THAT = *endFrame-1\n"
                  "M=M-1\n"
                  "A=M\n"
                  "D=M\n"
                  "@THAT\n"
                  "M=D\n"
                  "@14 // THIS = *endFrame-2\n"
                  "M=M-1\n"
                  "A=M\n"
                  "D=M\n"
                  "@THIS\n"
                  "M=D\n"
                  "@14 // ARG = *endFrame-3\n"
                  "M=M-1\n"
                  "A=M\n"
                  "D=M\n"
                  "@ARG\n"
                  "M=D\n"
                  "@14 // LCL = *endFrame-4\n"
                  "M=M-1\n"
                  "A=M\n"
                  "D=M\n"
                  "@LCL\n"
                  "M=D\n"
                  "@15 // GOTO retAddr\n"
                  "A=M\n"
                  "0;JMP\n")

        return output

    def c_call(self, command):
        functionName, nArgs = command["args"]

        callNo = self.functionCalls[functionName]
        self.functionCalls[functionName] += 1
        functionName = functionName
        argsIndex = int(nArgs)+5
        original = command["command"]
        callNo = callNo

        output = (f"@{functionName}$ret.{callNo} // push returnAddr // {original}\n"
                  "D=A\n"
                  "@SP\n"
                  "M=M+1\n"
                  "A=M-1\n"
                  "M=D\n"
                  "@LCL // push LCL\n"
                  "D=M\n"
                  "@SP\n"
                  "M=M+1\n"
                  "A=M-1\n"
                  "M=D\n"
                  "@ARG // push ARG\n"
                  "D=M\n"
                  "@SP\n"
                  "M=M+1\n"
                  "A=M-1\n"
                  "M=D\n"
                  "@THIS // push THIS\n"
                  "D=M\n"
                  "@SP\n"
                  "M=M+1\n"
                  "A=M-1\n"
                  "M=D\n"
                  "@THAT // push THAT\n"
                  "D=M\n"
                  "@SP\n"
                  "M=M+1\n"
                  "A=M-1\n"
                  "M=D\n"
                  f"@{argsIndex} // ARG = SP-5-nArgs\n"
                  "D=A\n"
                  "@SP\n"
                  "D=M-D\n"
                  "@ARG\n"
                  "M=D\n"
                  "@SP // LCL = SP\n"
                  "D=M\n"
                  "@LCL\n"
                  "M=D\n"
                  f"@{functionName}\n"
                  "0;JMP\n"
                  f"({functionName}$ret.{callNo})\n")
        return output
