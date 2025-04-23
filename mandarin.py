import sys
import subprocess
from enum import Enum, auto
import types
import typing
import os
import glob
from dataclasses import dataclass

HEAP_SIZE = 64 * 1<<10

__HELP_STR__ ='''
commandline usage: mandarin.py <[c <input_file> <c_options>]|[s <input_file> <s_options>]>

<input_file> -> *.mand

<c_options> -> [-o <output_file>]

<s_options> -> [-s <output_file>]

    -o -> specify output file for compilation
    -s -> specify output file for outputting of simulation data output
    
'''

class CMDCOL:
    GOOD = '\033[92m'
    OKAY = '\033[96m'
    OK = '\033[94m'
    WARN = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    LINE = '\033[4m'
    END = '\033[0m'

class TOKENS(Enum):
    WORD        = auto()
    OPERAND     = auto()
    NAME        = auto()
    TYPE        = auto()
    CODEOPEN    = auto()
    CODECLOSE   = auto()
    NUM         = auto()
    COUNT       = auto()

class OP(Enum):
    NUM         = auto()
    SET         = auto()
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    IF          = auto()
    WHILE       = auto()
    JUMP        = auto()
    COPY        = auto()
    PRINT       = auto()
    PRINT_NL    = auto()
    PRINT_AND_NL= auto()
    PRINT_CHAR  = auto()
    VAR         = auto()
    TYPE        = auto()
    COUNT       = auto()

class DT(Enum):
    UINT8       = auto()
    COUNT       = auto()

class CB(Enum):
    COMPILETIME = auto()
    CONDITION   = auto()
    RESOLVE     = auto()
    CODE        = auto()
    COUNT       = auto()
@dataclass
class Token:
    type:       TOKENS
    name:       str

@dataclass
class Var:
    type: DT
    name: str
class codeBlock:
    id:         int = -1
    type:       CB = CB.COMPILETIME
    tokens:     list[Token | typing.Self] = []
    vars:       list[Var]

    def __init__(self, id = -1, tokens = [], vars = []):
        self.id = id
        self.tokens = tokens
        self.vars = vars

@dataclass
class OpType:
    type:       OP
    loc:        int
    value:      typing.Any = None
    jmp:        int = -1
    codeblock:  codeBlock = codeBlock()

class Error(Enum):
    CMD         = auto()
    ENUM        = auto()
    PARSE       = auto()
    TOKENIZE    = auto()
    COMPILE     = auto()
    SIMULATE    = auto()

def error(errorType: int, errorStr: str, exitAfter: bool = True):
    sys.stderr.write(" >>> " + errorStr + f"{CMDCOL.END}\n")
    if(errorType == Error.CMD):
        sys.stdout.write(__HELP_STR__ + f"{CMDCOL.END}\n")
    if exitAfter:
        exit(1)

def compile_data(data: list[dict]):
    assert False, "not implemented yet"

def simulate_data(data: list[dict], out = sys.stdout):
    assert OP.COUNT.value == 16, "Exhaustive token counter protection"
    heap = bytearray(HEAP_SIZE)
    stack = []
    overjump = False
    ip = 0
    while ip < len(data):
        x = data[ip]
        match x.type:
            case OP.NUM:
                stack.append(int(x.value))
            case OP.ADD:
                a = stack.pop()
                b = stack.pop()
                stack.append(b+a)
            case OP.SUB:
                a = stack.pop()
                b = stack.pop()
                stack.append(b-a)
            case OP.MUL:
                a = stack.pop()
                b = stack.pop()
                stack.append(b*a)
            case OP.IF:
                a = stack.pop()
                if not a:
                    ip = x.jmp
                    continue
            case OP.WHILE:
                pass
            case OP.DIACRITIC:
                a = stack.pop()
                if not a:
                    ip = x.jmp
                    overjump = True
                    continue
            case OP.END:
                if x.jmp != -1 and not overjump:
                    ip = x.jmp
                    continue
                overjump = False
            case OP.COPY:
                a = stack.pop()
                stack.append(a)
                stack.append(a)
            case OP.PRINT:
                a = stack.pop()
                out.write(str(a))
            case OP.PRINT_NL:
                out.write('\n')
            case OP.PRINT_AND_NL:
                a = stack.pop()
                out.write(str(a))
                out.write('\n')
            case OP.PRINT_CHAR:
                a = stack.pop()
                out.write(chr(int(a)))
            case OP.VAR | OP.SET | OP.UINT8:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
            case _:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
        ip += 1

def unpack(arr: list) -> tuple[typing.Any, list]:
    if len(argv) < 1:
        error(Error.CMD, "Not enough arguments!")
    return (arr[0], arr[1:])

alone_token = {
    "."     : TOKENS.WORD,
    ".n"    : TOKENS.WORD,
    "..n"   : TOKENS.WORD,
    ".c"    : TOKENS.WORD,
}

indifferent_token = {
    "if"    : TOKENS.WORD,
    "while" : TOKENS.WORD,
    "copy"  : TOKENS.WORD,
    "u8"    : TOKENS.TYPE,
    "="     : TOKENS.OPERAND,
    "+"     : TOKENS.OPERAND,
    "-"     : TOKENS.OPERAND,
    "*"     : TOKENS.OPERAND,
    "{"     : TOKENS.CODEOPEN,
    "("     : TOKENS.CODEOPEN,
    "}"     : TOKENS.CODECLOSE,
    ")"     : TOKENS.CODECLOSE,
}

operand_map = {
    "."     : OP.PRINT,
    ".n"    : OP.PRINT_NL,
    "..n"   : OP.PRINT_AND_NL,
    ".c"    : OP.PRINT_CHAR,
    "if"    : OP.IF,
    "while" : OP.WHILE,
    "copy"  : OP.COPY,
    "="     : OP.SET,
    "+"     : OP.ADD,
    "-"     : OP.SUB,
    "*"     : OP.MUL,
}

type_map = {
    "u8"    : DT.UINT8
}

unprotected_static_token = {
}

def resolve_structures(data: list[OpType]) -> list[OpType]:
    ret = []

    index = 0
    while index < len(data):
        pass
    
    return ret

def resolve_names(data: list[OpType]) -> list[OpType]:
    index = 0
    tmp: OpType
    num: OpType
    while index < len(data):
        if data[index].type == OP.SET:
            if 0 < index < len(data)-1:
                if data[index-1].type == OP.NUM and data[index+1].type == OP.VAR:
                    index -= 1
                    data.pop(index+1)
                    num = data[index].value
                    tmp = data.pop(index+1)
                    secIndex = index
                    while secIndex < len(data):
                        if data[secIndex].type == OP.SET:
                            if 0 < secIndex < len(data)-1:
                                if data[secIndex+1].type == OP.VAR and data[secIndex+1].value == tmp.value and data[secIndex-1].type == OP.NUM:
                                    secIndex -= 1
                                    data.pop(secIndex+1)
                                    data.pop(secIndex+1)
                                    num = data[secIndex].value
                                    secIndex -= 3
                                else:
                                    error(Error.PARSE, "Wrong usage of `=` during reassigment, couldn't find number ")
                            else:
                                error(Error.PARSE, "Wrong usage of `=` during reassigment")
                        if data[secIndex].type == OP.VAR and data[secIndex].value == tmp.value:
                            data[secIndex].type = OP.NUM
                            data[secIndex].value = num
                        secIndex += 1
                else:
                    error(Error.PARSE, "Wrong usage of `=`, couldn't find number or/and var name at either side\n ip-1 > %s | ip+1 > %s" % (data[index-1].type.name,data[index+1].type.name))
            else:
                error(Error.PARSE, "Wrong usage of `=`, found at the end or begining of file")
        index += 1
    return data


def Parse_jump(data: list[OpType]) -> list[OpType]:
    assert OP.COUNT.value == 16, "Exhaustive token jump parsing protection"
    end_stack = []
    index = 0
    while index < len(data):
        if data[index].type == OP.IF:
            end_stack.append(index)
        if data[index].type == OP.WHILE:
            end_stack.append(index)
        if data[index].type == OP.DIACRITIC:
            pass
            end_stack.append(index)
        if data[index].type == OP.END:
            if len(end_stack):
                x = end_stack.pop()
                match data[x].type:
                    case OP.IF:
                        data[x].jmp = index
                    case OP.WHILE:
                        error(Error.PARSE, "`end` after while without `:` symbol!")
                    case OP.DIACRITIC:
                        if len(end_stack):
                            y = end_stack.pop()
                            if data[y].type == OP.WHILE:
                                data[x].jmp = index
                                data[index].jmp = y
                            else:
                                error(Error.PARSE, "use of `:` without `while` beforehand!")
                    case _:
                        error(Error.TOKENIZE, "unreachable or not implemented")
        index += 1
    return data

def Secound_token_parse(data: codeBlock, index_offset: int = 0) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=16):
        error(Error.ENUM, f"{CMDCOL.BOLD}{CMDCOL.FAIL}Exhaustive operation parsing protection in Secound_token_parse{CMDCOL.END}{CMDCOL.OKAY} >>> expected `{CMDCOL.GOOD}{m}{CMDCOL.OKAY}` | got `{CMDCOL.FAIL}{n}{CMDCOL.OKAY}`")
    if (n:=CB.COUNT.value) != (m:=5):
        error(Error.ENUM, f"{CMDCOL.BOLD}{CMDCOL.FAIL}Exhaustive codeblock parsing protection in Secound_token_parse{CMDCOL.END}{CMDCOL.OKAY} >>> expected `{CMDCOL.GOOD}{m}{CMDCOL.OKAY}` | got `{CMDCOL.FAIL}{n}{CMDCOL.OKAY}`")
    
    index = 0
    while index < len(data.tokens):
        match data.tokens[index].type:
            case OP.TYPE:
                if index+1 < len(data.tokens):
                    if data.tokens[index+1].type == OP.VAR:
                        if not (n:=Var(data.tokens[index].value, data.tokens[index+1].value)) in data.vars:
                            data.vars.append(n)
                            data.tokens.pop(index)
                            index += 1
                        else:
                            error(Error.PARSE, f"var already stated")
                    else:
                        error(Error.PARSE, f"no var token after type")
                else:
                    error(Error.PARSE, f"type at the end of file")
            case OP.VAR:
                if not (n:=data.tokens[index].value) in [x.name for x in data.vars]:
                    error(Error.PARSE, f"{CMDCOL.FAIL}Variable `{CMDCOL.OKAY}{CMDCOL.LINE}{n}{CMDCOL.END}{CMDCOL.FAIL}` stated without assigment!")

            case CB.CODE | CB.CONDITION | CB.RESOLVE:
                data.tokens[index].vars = data.vars.copy()
                data.tokens[index] = Secound_token_parse(data.tokens[index], index)
        index += 1
    return data
        
def First_token_parse(data: list[Token]) -> codeBlock:

    if (n:=OP.COUNT.value) != (m:=16):
        error(Error.ENUM, f"{CMDCOL.BOLD}{CMDCOL.FAIL}Exhaustive operation parsing protection in First_token_parse{CMDCOL.END}{CMDCOL.OKAY} >>> expected `{CMDCOL.GOOD}{m}{CMDCOL.OKAY}` | got `{CMDCOL.FAIL}{n}{CMDCOL.OKAY}`")


    ret: codeBlock = codeBlock(0)

    codeBlock_stack: list[codeBlock] = [ret]
    
    codeblock_id_index = 1

    index_offset = 0
    index = 0
    while index < len(data):
        match data[index].type:
            case TOKENS.WORD | TOKENS.OPERAND:
                codeBlock_stack[-1].tokens.append(OpType(operand_map[data[index].name], index + index_offset))
            case TOKENS.NAME:
                codeBlock_stack[-1].tokens.append(OpType(OP.VAR, index + index_offset, data[index].name))
            case TOKENS.NUM:
                codeBlock_stack[-1].tokens.append(OpType(OP.NUM, index + index_offset, int(data[index].name)))
            case TOKENS.TYPE:
                codeBlock_stack[-1].tokens.append(OpType(OP.TYPE, index + index_offset, type_map[data[index].name]))
            case TOKENS.CODEOPEN:
                codeBlock_stack.append(codeBlock(codeblock_id_index, [], []))
                codeblock_id_index += 1
                index_offset -= 1
            case TOKENS.CODECLOSE:
                codeBlock_stack[-2].tokens.append(codeBlock_stack.pop())
                index_offset -= 1
            case _:
                error(Error.PARSE, "unreachable!")
        index += 1
    return codeBlock_stack[-1]

def Parse_token(file_path: str, loc: tuple[int, int], data: str) -> list[Token]:
    if (n:=TOKENS.COUNT.value) != 8:
        error(Error.ENUM, f"{CMDCOL.BOLD}{CMDCOL.FAIL}Exhaustive token parsing protection in Parse_token{CMDCOL.END}{CMDCOL.OKAY} >>> expected `{CMDCOL.GOOD}{16}{CMDCOL.OKAY}` | got `{CMDCOL.FAIL}{n}{CMDCOL.OKAY}`")

    ret: list[Token] = []
    if data in alone_token:
        ret += [Token(alone_token[data], data)]
        data = ""
    elif data in indifferent_token:
        ret += [Token(indifferent_token[data], data)]
        data = ""
    else:
        for x in list(alone_token.keys()):
            if data.startswith(x):
                error(Error.TOKENIZE, f"{CMDCOL.BOLD}{CMDCOL.FAIL}Error{CMDCOL.WARN} {file_path}:{loc[0]+1}:{loc[1]-len(data)} keyword starts with disallowed token {x} in {data}{CMDCOL.END}")
        for x in indifferent_token.keys():
            if data.find(x) != -1:
                (before, token, after) = data.partition(x)
                ret += Parse_token(file_path, loc, before)
                if before:
                    ret += [Token(indifferent_token[token], token)]
                if after:
                    ret += Parse_token(file_path, loc, after)
                data = ""

        if data.isnumeric():
            ret += [Token(TOKENS.NUM, data)]
            data = ""
        if data:
            print(data)
            if data[0].isdigit():
                error(Error.TOKENIZE, f"name token cannot begin with a number")
            ret += [Token(TOKENS.NAME, data)]
            #assert False, "unknown keyword %s" % (data)
    
    for x in ret:
        print(x)

    return ret

def Parse_line(file_path: str, line: int, data: str) -> list:
    ret = []
    t = ""
    index = 0
    if data.find("//") != -1:
        (before, _, _) = data.partition("//")
        data = before
    while index < len(data):
        if data[index].isspace():
            ret += Parse_token(file_path, (line, index+1), t)
            t = ""
        else:
            t = t + data[index]
        index += 1
    if t:
        ret += Parse_token(file_path, (line, index+1), t)
    return ret

def Parse_file(input: str) -> list:
    data = []
    with open(input, 'r') as f:
        data = f.readlines()
    for x in Secound_token_parse(First_token_parse([op for row, line in enumerate(data) for op in Parse_line(input, row, line)])).vars:
        print(x)
    #return Parse_jump(resolve_names([op for row, line in enumerate(data) for op in Parse_line(input, row, line)]))

# ------------------------------------------------------
# -------------------- TEST SECTION --------------------
# ------------------------------------------------------
class dataHolder:
    data: str = ""
    def write(self, string):
        self.data = self.data + string
    
    def compare_with_file(self, file_path):
        data: str = ""
        with open(file_path, 'r') as f:
            data = f.read()
        return data == self.data

def record_test():
    for x in glob.glob("./tests/*.mand"):
        with open(x[:-5]+".txt", "w") as f:
            simulate_data(Parse_file(x), out = f)

def compare_test():
    for x in glob.glob("./tests/*.mand"):
        dh: dataHolder = dataHolder()
        simulate_data(Parse_file(x), out = dh)
        if not dh.compare_with_file(x[:-5]+".txt"):
            sys.stderr.write(f"{CMDCOL.LINE}{x}{CMDCOL.END} {CMDCOL.FAIL}Test Failed{CMDCOL.END}\n")
        else:
            sys.stdout.write(f"{CMDCOL.LINE}{x}{CMDCOL.END} {CMDCOL.GOOD}Passed{CMDCOL.END}\n")

# CMD LINE

if __name__ == "__main__":
    argv: list[str] = sys.argv[1:]
    if len(argv) < 1:
        error(Error.CMD, "No Commandline options provided")
    option, argv = unpack(argv)

    match option:
        case 'c':
            input_file, argv = unpack(argv)

            if not os.path.isfile(input_file):
                error(Error.CMD, "Wrong file provided, compiller couldn't find file at a `%s` location" % (input_file))
            data = Parse_file(input_file)
            
            compile_data(data)
        case 's':
            input_file, argv = unpack(argv)

            if not os.path.isfile(input_file):
                error(Error.CMD, "Wrong file provided, compiller couldn't find file at a `%s` location" % (input_file))
            data = Parse_file(input_file)
            
            #simulate_data(data)
        case 't':
            test_type: str

            if len(argv) > 0:
                test_type, argv = unpack(argv)
            else:
                test_type = "compare"

            match test_type:
                case "record":
                    record_test()
                case "compare":
                    compare_test()
                case _:
                    error(Error.CMD, "Wrong test type provided, expected `record` or `compare`, got `%s`!" % (test_type)) 
        case _:
            error(Error.CMD, "Wrong mode provided, expected `c` or `s`, got `%s`!" % (option))
