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
        self.file.write( ("@256 // init\n"
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
                "D=D-1\n") )

    def setFilename(self, fileURI):
        self.filename = os.path.basename(fileURI).partition(".vm")[0]

    def write(self, command):
        self.file.write(self.handlers[command["commandType"]](command))

    def c_push(self, command):
        original = command["command"]
        args = command["args"]
        if args[0] == "constant":
            return ("@{constant} // {original}\n"
                    "D=A\n"
                    "@SP\n"
                    "A=M\n"
                    "M=D\n"
                    "@SP\n"
                    "M=M+1\n").format(constant=args[1], original=original)
        elif args[0] in self.stacks:
            return ("@{index} // {original}\n"
                    "D=A\n"
                    "@{stack}\n"
                    "A=D+M\n"
                    "D=M\n"
                    "@SP\n"
                    "A=M\n"
                    "M=D\n"
                    "@SP\n"
                    "M=M+1\n").format(index=args[1], original=original, stack=self.stacks[args[0]])
        elif args[0] == "static":
            output = ("@{filename}.{index} // {original}\n"
                      "D=M\n"
                      "@SP\n"
                      "A=M\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M+1\n")
            output = output.format(
                filename=self.filename, index=args[1], original=original)
            return output
        elif args[0] == "pointer":
            location = "THIS" if not int(args[1]) else "THAT"
            output = ("@{location} // {original}\n"
                      "D=M\n"
                      "@SP\n"
                      "A=M\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M+1\n")
            output = output.format(location=location, original=original)
            return output
        elif args[0] == "temp":
            index = 5+int(args[1])
            output = ("@{index} // {original}\n"
                      "D=M\n"
                      "@SP\n"
                      "A=M\n"
                      "M=D\n"
                      "@SP\n"
                      "M=M+1\n")
            output = output.format(index=index, original=original)
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
            output = ("@SP // {command}\n"
                      "A=M-1\n"
                      "M={operator}M\n")
            return output.format(operator=unary[command["command"]], command=command["command"])
        elif command["command"] in binary:  # binary operators
            output = ("@SP // {command}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "A=A-1\n"
                      "M=M{operation}D\n")
            return output.format(operation=binary[command["command"]], command=command["command"])
        elif command["command"] in boolean:
            output = ("@SP // {command}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "A=A-1\n"
                      "D=M-D\n"
                      "@SKIP.{count}\n"
                      "D;{operation}\n"
                      "@SP\n"
                      "A=M-1\n"
                      "M=0\n"
                      "@END.{count}\n"
                      "0;JMP\n"
                      "(SKIP.{count})\n"
                      "@SP\n"
                      "A=M-1\n"
                      "M=-1\n"
                      "(END.{count})\n")
            output = output.format(
                operation=boolean[command["command"]], count=self.arithmeticCount, command=command["command"])
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
            output = ("@{index} // {original}\n"
                      "D=A\n"
                      "@{stack}\n"
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
            output = output.format(original=original, stack=stack, index=index)
        elif stack == "static":
            output = ("@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "@{filename}.{index}\n"
                      "M=D\n")
            output = output.format(
                original=original, filename=self.filename, index=index)
        elif stack == "pointer":
            if index == "0":
                stack = "THIS"
            elif index == "1":
                stack = "THAT"
            output = ("@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "@{stack}\n"
                      "M=D\n")
            output = output.format(original=original, stack=stack)
        elif stack == "temp":
            stack = int(index)+5
            output = ("@SP // {original}\n"
                      "M=M-1\n"
                      "A=M\n"
                      "D=M\n"
                      "@{stack}\n"
                      "M=D\n")
            output = output.format(original=original, stack=stack)
        else:
            raise Exception('Invalid pop location: "{original}"'.format(original=command["command"]))
        return output

    def c_label(self, command):
        return "({label}) //{original}\n".format(label=command["args"][0], original=command["command"])

    def c_goto(self, command):
        return ("@{label} // {original}\n"
                "0;JMP\n").format(label=command["args"][0], original=command["command"])

    def c_if(self, command):
        return ("@SP // {original}\n"
                "M=M-1\n"
                "A=M\n"
                "D=M\n"
                "@{label}\n"
                "D;JNE\n").format(label=command["args"][0], original=command["command"])

    def c_function(self, command):
        output = "({functionName}) // {original}\n".format(
            functionName=command["args"][0], original=command["command"])
        nVars = ("@SP\n"
                 "M=M+1\n"
                 "A=M-1\n"
                 "M=0\n") * int(command["args"][1])
        return output + nVars

    def c_return(self, command):
        output = ("@LCL // {original}\n"
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

        return output.format(original=command["command"])

    def c_call(self, command):
        functionName, nArgs = command["args"]
        
        callNo = self.functionCalls[functionName]
        self.functionCalls[functionName] += 1

        output = ("@{functionName}$ret.{callNo} // push returnAddr // {original}\n"
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
                  "@{argsIndex} // ARG = SP-5-nArgs\n"
                  "D=A\n"
                  "@SP\n"
                  "D=M-D\n"
                  "@ARG\n"
                  "M=D\n"
                  "@SP // LCL = SP\n"
                  "D=M\n"
                  "@LCL\n"
                  "M=D\n"
                  "@{functionName}\n"
                  "0;JMP\n"
                  "({functionName}$ret.{callNo})\n")
        return output.format(functionName=functionName, argsIndex=int(nArgs)+5, original=command["command"], callNo=callNo)
