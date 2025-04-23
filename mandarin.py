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

__iota_counter__ = 0
def iota(reset=False):
    global __iota_counter__
    if reset:
        __iota_counter__ = 0
    ret = __iota_counter__
    __iota_counter__ += 1
    return ret


class PDO(Enum):
    RAW_INT     = auto()
    VAR_SET     = auto()

class OP(Enum):
    NUM         = auto()
    SET         = auto()
    ADD         = auto()
    SUB         = auto()
    MUL         = auto()
    IF          = auto()
    WHILE       = auto()
    DIACRITIC   = auto()
    END         = auto()
    COPY        = auto()
    PRINT       = auto()
    PRINT_NL    = auto()
    PRINT_AND_NL= auto()
    PRINT_CHAR  = auto()
    VAR         = auto()
    COUNT       = auto()

@dataclass
class OpType:
    type : OP
    loc : int
    value : typing.Any
    jmp : int = -1
    sibling : int | None = None

class Error(Enum):
    CMD         = auto()
    PARSE       = auto()
    TOKENIZE    = auto()
    COMPILE     = auto()
    SIMULATE    = auto()

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
            case OP.VAR:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
            case OP.SET:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
            case _:
                assert False, "unreachable %s | ip -> %d" % (x.type.name, ip)
        ip += 1

def error(errorType: int, errorStr: str, exitAfter: bool = True):
    sys.stderr.write(" >>> " + errorStr + "\n")
    if(errorType == Error.CMD):
        sys.stdout.write(__HELP_STR__ + "\n")
    if exitAfter:
        exit(1)

def unpack(arr: list) -> tuple[typing.Any, list]:
    if len(argv) < 1:
        error(Error.CMD, "Not enough arguments!")
    return (arr[0], arr[1:])

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



def resolve_structures(data: list[OpType]) -> list[OpType]:
    ret = []

    index = 0
    while index < len(data):
        pass
    

    return ret

protected_static_token = {
    "."     : OP.PRINT,
    ".n"    : OP.PRINT_NL,
    "..n"   : OP.PRINT_AND_NL,
    ".c"    : OP.PRINT_CHAR,
    "if"    : OP.IF,
    "while" : OP.WHILE,
    "end"   : OP.END,
    "copy"  : OP.COPY,
}

assisted_static_token = {
    "="     : OP.SET,
    "+"     : OP.ADD,
    "-"     : OP.SUB,
    "*"     : OP.MUL,
    ":"     : OP.DIACRITIC,
}

unprotected_static_token = {
}

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

def Parse_token(loc: tuple[int, int], data: str) -> list[OpType]:
    assert OP.COUNT.value == 16, "Exhaustive token parsing protection"

    ret: list[OpType] = []

    if data in protected_static_token:
        ret += [OpType(protected_static_token[data], loc, data, -1)]
        data = ""
    elif data in assisted_static_token:
        ret += [OpType(assisted_static_token[data], loc, data, -1)]
        data = ""
    elif data in unprotected_static_token:
        ret += [OpType(unprotected_static_token[data], loc, data, -1)]
        data = ""
    else:
        for x in list(protected_static_token.keys())+list(assisted_static_token.keys()):
            if data.startswith(x):
                assert False, "keyword starts with disallowed token %s | %s" % (x, data)
        for x in assisted_static_token.keys():
            if data.find(x) != -1:
                (before, token, after) = data.partition(x)
                ret += Parse_token(loc, before)
                ret += [OpType(assisted_static_token[token], loc, token, -1)]
                if after:
                    ret += Parse_token(loc, after)
                data = ""

        if data.isnumeric():
            ret += [OpType(OP.NUM, loc, int(data), -1)]
            data = ""
        if data:
            ret += [OpType(OP.VAR, loc, data, -1)]
            #assert False, "unknown keyword %s" % (data)
    
    return ret

def Parse_line(line: int, data: str) -> list:
    ret = []
    t = ""
    index = 0
    if data.find("//"):
        (before, _, _) = data.partition("//")
        data = before
    while index < len(data):
        if data[index].isspace():
            ret += Parse_token((line, index+1), t)
            t = ""
        else:
            t = t + data[index]
        index += 1
    if t:
        ret += Parse_token((line, index+1), t)
    return ret

def Parse_file(input: str) -> list:
    data = []
    with open(input, 'r') as f:
        data = f.readlines()
    return Parse_jump(resolve_names([op for row, line in enumerate(data) for op in Parse_line(row, line)]))

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
            
            simulate_data(data)
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
