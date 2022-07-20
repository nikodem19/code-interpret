import sys
import re
import argparse
import xml.etree.ElementTree as ET

##  Regexy pre vsetky potrebne formaty
symb = "^(nil)(@)(nil)$|^(bool)(@)(true|false)$|^(int)(@)(\S+)$|^(string)(@)([\S]*)$|^(var@)(GF|LF|TF)(@)([a-zA-Z_\-$&%*!?]+[a-zA-Z0-9_\-$&%*!?]*)$"
label = "^(label@([a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*))$"
types = "^type@(bool|int|string)$"
var = "^(var@)(GF|LF|TF)(@)([a-zA-Z_\-$&%*!?]+[a-zA-Z0-9_\-$&%*!?]*)$"

##  Rozdelenie operacii
operationsWithNone = ["CREATEFRAME", "PUSHFRAME", "POPFRAME", "RETURN", "BREAK"]
operationsWithOne = ["DEFVAR", "CALL", "PUSHS", "POPS", "WRITE", "LABEL", "JUMP", "EXIT", "DPRINT"]
operationsWithTwo = ["MOVE", "INT2CHAR", "READ", "STRLEN", "TYPE", "NOT"]
operationsWithThree = ["ADD", "SUB", "MUL", "IDIV", "LT", "GT", "EQ", "AND", "OR", "STRI2INT", "CONCAT", "GETCHAR", "SETCHAR", "JUMPIFEQ", "JUMPIFNEQ"]

##  Vytvorenie glob premennych
tempFrame = None
locFrame = None
globFrame = {}
stack = []

inputCode = None
Input = None

##   Prepísanie error message
class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise


##  Skontroluje argumenty a vstupy
##  @return argsArray   array s ulozenymi argumentami
def parseArguments():
    argParser = ArgumentParser(description="argument parser")
    argsArray = {}

    try:
        argParser.add_argument('--input', action='append')
        argParser.add_argument('--source', action='append')
        args = argParser.parse_args()

        if (args.input is not None):
            if (len(args.input) > 1):
                argParser.error(1)
            argsArray["input"] = args.input[0]

        if (args.source is not None):
            if (len(args.source) > 1 or (not args.source[0])):
                argParser.error(1)
            argsArray["source"] = args.source[0]
    except:
        sys.exit(10)
    return argsArray


## Načíta kod zo standardneho vstupu
## @return code  načítaný kód
def loadStdin():
    code = ""
    for line in sys.stdin:
        code += line
    return code


##  Načíta vstupný súbor a skontroluje
##  @param  file        súbor s ktorým precujeme
##  @return inputFile   vracia otvorený a skontrolovaný subor
def setFile(file):
    try:
        inputFile = open(file, 'r').read()
        return inputFile
    except:
        sys.exit(11)


##  Skontrolovanie syntax pomocou Elementtree knihovne a vytvorenie slovníka z xml vstupu
##  @param  code        xml reprezentácia kodu
##  @return dictionary  výsledný slovnik
def checkLexical(code):
    size = 1
    try:
        tree = ET.fromstring(code)
    except:
        exit(31)
    if (tree.tag != 'program' or tree.attrib['language'] != "IPPcode20"):
        sys.exit(32)
    if ('language' not in tree.attrib):
        sys.exit(32)
    if ('description' in tree.attrib):
        size += 1
    if (len(tree.attrib) != size):
        sys.exit(32)
    if ('name' in tree.attrib):
        size += 1
    dictionary = dict()
    for instr in tree:
        if (instr.tag != "instruction"):
            sys.exit(32)
        if ((len(instr.attrib) != 2) or ('order' not in instr.attrib) or ('opcode' not in instr.attrib)):
            sys.exit(32)
        order = int(instr.attrib['order'].strip())
        if (order in dictionary):
            sys.exit(32)
        dictionary[order] = {}
        dictionary[order] = instr.attrib
        dictionary[order]['args'] = {}
        argTags = {}
        for arg in instr:
            if arg.tag in argTags:
                sys.exit(32)
            argTags[arg.tag] = 1
            dictionary[order]['args'][arg.tag] = {}
            if (len(arg.attrib) != 1 or arg.attrib['type'] is None):
                sys.exit(32)
            if (arg.text is None):
                if arg.attrib['type'] == "string":
                    arg.text = ""
                else:
                    sys.exit(32)
            if ("#" in arg.text):
                sys.exit(32)
            dictionary[order]['args'][arg.tag]['type'] = arg.attrib['type'].strip()
            dictionary[order]['args'][arg.tag]['value'] = arg.text.strip()
    return dictionary


##  Skontroluje poradie parametrov v instrukciach
##  @param  code    upravovany kod
##  @return         koniec programu
def checkOrder(code):
    arr = []
    orderArr = []

    for x in range(1, len(code) + 1):
        arr.append(x)
    try:
        for value, key in code.items():
            if (int(key['order']) not in arr):
                raise
            else:
                if (int(key['order']) in orderArr):
                    raise
                orderArr.append(int(key['order']))
    except:
        sys.exit(32)
    return


##  Pomocou regexov skontroluje funkcia formát argumentov instrukcii
##  @param  args    argumenty instrukcii
##  @param  type    blizsie specifikovane info o instrukciach
def checkFormat(args, type):
    if (len(type) == 1):
        if (type == "l"): # label
            if (re.match(label, args[0]) == None):
                sys.exit(32)
        if (type == "s"): # symbol
            if (re.match(symb, args[0]) == None):
                sys.exit(32)
        if (type == "v"): # variable
            if (re.match(var, args[0]) == None):
                sys.exit(32)
    elif (len(type) == 2):
        if (re.match(var, args[0]) == None):
            sys.exit(32)
        if (type == "vs"): # variable , symbol
            if (re.match(symb, args[1]) == None):
                sys.exit(32)
        if (type == "vt"): # variable, types
            if (re.match(types, args[1]) == None):
                sys.exit(32)
    elif (len(type) == 3):
        if (type == "vss"): # variable, symbol, symbol
            if (re.match(var, args[0]) == None):
                sys.exit(32)
        elif (type == "lss"): # label, symbol, symbol
            if (re.match(label, args[0]) == None):
                sys.exit(32)
        if (re.match(symb, args[1]) == None or
                re.match(symb, args[2]) == None):
            sys.exit(32)
    else:
        sys.exit(32)


##  Kontrola syntax
##  @param  code            skontrolovany a upraveny kod
##  @return checkedCode     kod pripraveny pre interpret
def checkSyntax(code):
    checkOrder(code)
    checkedCode = {}

    for value, key in sorted(code.items()):
        key['opcode'] = key['opcode'].strip()
        if (len(key['args']) > 3):
            sys.exit(32)
        checkedCode[key['order']] = key['order']
        checkedCode[key['order']] = {}
        checkedCode[key['order']][0] = key['opcode']

        if (key['opcode'] in operationsWithNone):
            if (len(key['args']) != 0):
                sys.exit(32)

        elif (key['opcode'] in operationsWithOne):
            if (len(key['args']) != 1):
                sys.exit(32)
            format = [key['args']['arg1']['type'] + '@' + key['args']['arg1']['value']]
            if (key['opcode'] == "PUSHS" or key['opcode'] == "WRITE" or key['opcode'] == "EXIT" or key['opcode'] == "DPRINT"):
                checkFormat(format, "s")
            elif (key['opcode'] == "CALL" or key['opcode'] == "LABEL" or key['opcode'] == "JUMP"):
                checkFormat(format, "l")
            else:
                checkFormat(format, "v")
            checkedCode[key['order']][1] = format[0]

        elif (key['opcode'] in operationsWithTwo):
            if (len(key['args']) != 2):
                sys.exit(32)
            if ('arg1' not in key['args'] or 'arg2' not in key['args']):
                sys.exit(32)
            format = [key['args']['arg1']['type'] + '@' + key['args']['arg1']['value'], key['args']['arg2']['type'] + '@' + key['args']['arg2']['value']]
            if (key['opcode'] == "READ"):
                checkFormat(format, "vt")
            else:
                checkFormat(format, "vs")
            checkedCode[key['order']][1] = format[0]
            checkedCode[key['order']][2] = format[1]

        elif (key['opcode'] in operationsWithThree):
            if (len(key['args']) != 3):
                sys.exit(32)
            if ('arg1' not in key['args'] or 'arg2' not in key['args'] or 'arg3' not in key['args']):
                sys.exit(32)
            format = [key['args']['arg1']['type'] + '@' + key['args']['arg1']['value'], key['args']['arg2']['type'] + '@' + key['args']['arg2']['value'], key['args']['arg3']['type'] + '@' + key['args']['arg3']['value']]
            if (key['opcode'] == "JUMPIFEQ" or key['opcode'] == "JUMPIFNEQ"):
                checkFormat(format, "lss")
            else:
                checkFormat(format, "vss")
            checkedCode[key['order']][1] = format[0]
            checkedCode[key['order']][2] = format[1]
            checkedCode[key['order']][3] = format[2]
        else:
            sys.exit(32)
    return checkedCode


##  Pripraví kod pre interpret
##  @param  code    skontrolovany kod
##  @return values  kod pripraveny na interpret
def editCode(code):
    values = list(code.values())
    for command in values:
        i = 0
        while i != len(command):
            if (command[i].count("@") == 2):
                command[i] = command[i].split("@")
                command[i] = command[i][1] + "@" + command[i][2]
            i+=1
    return values


##  Funkcia hlada premennu vo framoch
##  @param  var       hladana premenna
##  @param  frame     ramec s ktorym pracujeme
##  @return item      hladany item
def searchFrames(var, frame):
    global tempFrame, locFrame, globFrame
    if (frame == None):
        sys.exit(55)

    if isinstance(frame, dict):
        for key, item in frame.items():
            if item[0] == var[1]:
                return item
    else:
        for item in frame:
            if (item[0] == var[1]):
                return item
    sys.exit(0)


##  Získa atributy ako typ a hodnotu zadaneho symbolu
##   @param  symb            symbol, ktoremu priradujeme typ a hodnotu
##   @param  NeedNone=False  ignorovanie prazdneho argumentu
##   @return type, value     typ a hodnota zadaneho symbolu
def getAttributes(symb, needNone=False):
    try:
        if symb[0] == "TF":
            value = searchFrames(symb, tempFrame)[2]
            type = searchFrames(symb, tempFrame)[1]
        elif symb[0] == "LF":
            value = searchFrames(symb, locFrame[-1])[2]
            type = searchFrames(symb, locFrame[-1])[1]
        elif symb[0] == "GF":
            value = searchFrames(symb, globFrame)[2]
            type = searchFrames(symb, globFrame)[1]
        else:
            value = symb[1]
            type = symb[0]
    except (TypeError, IndexError, AttributeError):
        sys.exit(55)
    if (needNone is False and (type is None or value is None)):
        sys.exit(56)
    return type, value


##  Zmeni hodnotu a typ zadanej premennej
##  @param  var     upravovana premenna
##  @param  type    novy typnew
##  @param  value   nova hodnota
def changeVariable(var, type, value):
    try:
        if var[0] == "TF":
            index = tempFrame.index(searchFrames(var, tempFrame))
            tempFrame[index][1] = type
            tempFrame[index][2] = value
        elif var[0] == "LF":
            index = locFrame[-1].index(searchFrames(var, locFrame[-1]))
            locFrame[-1][index][1] = type
            locFrame[-1][index][2] = value
        elif var[0] == "GF":
            index = searchFrames(var, globFrame)
            globFrame[globFrame[index[0]][0]][1] = type
            globFrame[globFrame[index[0]][0]][2] = value
        else:
            sys.exit(32)
    except (TypeError, IndexError, AttributeError):
        sys.exit(55)

##  Vytvori premennu v zadanom ramci
##  @param  frame         ramec v ktorom pracujeme where the variable will be created
##  @param  variableName  meno premennej
def defvar(frame, variableName):
    global locFrame, tempFrame, globFrame
    try:
        if (frame == "TF"):
            if (tempFrame is None):
                sys.exit(55)
            if (variableName in frame):
                sys.exit(52)
            tempFrame.append([variableName, None, None])
        elif (frame == "LF"):
            if (locFrame is None):
                sys.exit(55)
            if (variableName in frame):
                sys.exit(52)
            locFrame[-1].append([variableName, None, None])
        elif (frame == "GF"):
            if (globFrame is None):
                sys.exit(55)
            if (variableName in frame):
                sys.exit(52)
            globFrame[variableName] = [variableName, None, None]
        else:
            sys.exit(55)
    except (TypeError, IndexError, AttributeError):
        sys.exit(55)

##  Nastaví premenne pri aritmetických operaciach
##  @params sym1,sym2                                 symboly s ktorymi pracujeme
##  @return sym1Type, sym1Value, sym2Type, sym2Value  vráti typ a hodnotu dvoch symbolov
def setSymbols(sym1, sym2):
    sym1Type, sym1Value = getAttributes(sym1)
    sym2Type, sym2Value = getAttributes(sym2)
    return sym1Type, sym1Value, sym2Type, sym2Value


##  Kontrola typov premennych
##  @params sym1,sym2            kontrolovane premenne
##  @param  type                 pozadovany typ
##  @return sym1Value, sym2Value hodnoty oboch symbolov
def checkArithmetic(sym1, sym2, type):
    sym1Type, sym1Value, sym2Type, sym2Value = setSymbols(sym1, sym2)
    if (sym1Type != sym2Type or sym1Type != type):
        sys.exit(53)
    return sym1Value, sym2Value


##  Pomocna funkcia na porovnavanie
##  @param  sym1,sym2  porovnavane symboly
##  @param  operator   rozhodujuci operator
##  @return value      vysledna hodnota
def compare(sym1, sym2, operator):
    value = "false"
    if (operator == "LT"):
        if sym1 < sym2:
            value = "true"
    elif (operator == "GT"):
        if sym1 > sym2:
            value = "true"
    elif (operator == "EQ"):
        if sym1 == sym2:
            value = "true"
    return value


##  Hlavna funkcia, ktora riesi logicke porovnavanie symbolov
##  @param  var             premenna na výsledok
##  @params symb1,symb2     porovnavane symboly
##  @param  operator        rozhodujuci operator
def ltgteq(var, symb1, symb2, operator):
    sym1Type, sym1Value = getAttributes(symb1)
    sym2Type, sym2Value = getAttributes(symb2)
    if (sym1Type != "nil" and sym2Type != "nil" and sym1Type != sym2Type):
        sys.exit(53)
    else:
        value = ""
        if (sym1Type == "nil" or sym2Type == "nil"):
            if (operator != "EQ"):
                sys.exit(53)
            value = compare(sym1Value, sym2Value, "EQ")
        elif sym1Type == "int":
            try:
                sym1Value = int(sym1Value)
                sym2Value = int(sym2Value)
                value = compare(sym1Value, sym2Value, operator)
            except:
                sys.exit(32)
        elif (sym1Type == "bool"): # zmeni stringy na bool
            if sym1Value == "true":
                sym1Value=True
            elif sym1Value == "false":
                return False
            if sym2Value == "true":
                sym2Value=True
            elif sym2Value == "false":
                return False
            value = compare(sym1Value, sym2Value, operator)
    changeVariable(var, "bool", value)


##  Getchar funkcia, ktora ziska znak na danej pozicii a ulozi ho do premennej
##  @param  var     vybrata premenna
##  @param  symb1   symbol, v ktorom hladame
##  @param  symb2   pozicia znaku
def getchar(var, symb1, symb2):
    sym1Type, sym1Value = getAttributes(symb1)
    sym2Type, sym2Value = getAttributes(symb2)
    if (sym1Type != "string" or sym2Type != "int"):
        sys.exit(53)
    try:
        value = sym1Value[int(sym2Value)]
    except:
        sys.exit(58)
    changeVariable(var, "string", value)


##  Setchar funkcia, nastavi znak na danej pozicii na nový
##  @param  var     premenna, v ktorej robime zmeny
##  @param  symb1   pozicia znaku
##  @param  symb2   novy znak
def setchar(var, symb1, symb2):
    varType, varValue = getAttributes(var)
    sym1Type, sym1Value = getAttributes(symb1)
    sym2Type, sym2Value = getAttributes(symb2)
    if (varType != "string" or sym1Type != "int" or sym2Type != "string"):
        sys.exit(53)
    try:
        value = list(varValue)
        value[int(sym1Value)] = sym2Value[0]
        value = ''.join(value)
    except:
        sys.exit(58)
    changeVariable(var, "string", value)


##  Výpis pomocneho textu
def printHelp():
    print(''' IPP code Interpret
            2019/2020 PROJECT
            Author: Nikodem Babirad
            Login: xbabir01

            IPP code Interpretation ''')
    sys.exit(0)


##  Interpretácia projektu, vykonáva instrukcie na zaklade ich mena
##  @param  code    kod pripraveny na interpretáciu
def codeInterpret(code):
    global tempFrame, locFrame, globFrame
    global inputCode, Input

    for instruction in code:
        i = 1
        while i != len(instruction):
            instruction[i] = instruction[i].split("@")
            i += 1
        if (instruction[0] == "MOVE"):
            sourceType, sourceValue = getAttributes(instruction[2])
            changeVariable(instruction[1], sourceType, sourceValue)

        elif (instruction[0] == "DEFVAR"):
            defvar(instruction[1][0], instruction[1][1])

        elif (instruction[0] == "CREATEFRAME"):
            if (tempFrame is None):
                tempFrame = []
            tempFrame.clear()

        elif (instruction[0] == "PUSHFRAME"):
            if (tempFrame is None):
                sys.exit(55)
            if (locFrame is None):
                locFrame = []
            locFrame.append(tempFrame)
            tempFrame = None

        elif (instruction[0] == "POPFRAME"):
            if (locFrame is None):
                sys.exit(55)
            if (tempFrame is None):
                tempFrame = []
            try:
                tempFrame = locFrame[-1]
            except IndexError:
                sys.exit(55)
            del locFrame[-1]

        elif (instruction[0] == "PUSHS"):
            type, value = getAttributes(instruction[1])
            stack.append([type, value])

        elif (instruction[0] == "POPS"):
            if not stack:
                sys.exit(56)
            changeVariable(instruction[1], stack[-1][0], stack[-1][1])
            del stack[-1]

        elif (instruction[0] == "ADD"):
            sym1Value, sym2Value = checkArithmetic(instruction[2], instruction[3], "int")
            changeVariable(instruction[1], "int", int(sym1Value) + int(sym2Value))

        elif (instruction[0] == "SUB"):
            sym1Value, sym2Value = checkArithmetic(instruction[2], instruction[3], "int")
            changeVariable(instruction[1], "int", int(sym1Value) - int(sym2Value))

        elif (instruction[0] == "MUL"):
            sym1Value, sym2Value = checkArithmetic(instruction[2], instruction[3], "int")
            changeVariable(instruction[1], "int", int(sym1Value) * int(sym2Value))

        elif (instruction[0] == "IDIV"):
            sym1Value, sym2Value = checkArithmetic(instruction[2], instruction[3], "int")
            if int(sym2Value) == 0:
                sys.exit(57)
            changeVariable(instruction[1], "int", int(sym1Value) / int(sym2Value))

        elif (instruction[0] == "LT"):
            ltgteq(instruction[1], instruction[2], instruction[3], "LT")

        elif (instruction[0] == "GT"):
            ltgteq(instruction[1], instruction[2], instruction[3], "GT")

        elif (instruction[0] == "EQ"):
            ltgteq(instruction[1], instruction[2], instruction[3], "EQ")

        elif (instruction[0] == "AND"):
            s1_type, s1_value = getAttributes(instruction[2])
            s2_type, s2_value = getAttributes(instruction[3])
            if (s1_type != "bool" or s2_type != "bool"):
                sys.exit(53)
            value = "false"
            if s1_value == "true" and s2_value == "true":
                value = "true"
            changeVariable(instruction[1], "bool", value)

        elif (instruction[0] == "OR"):
            s1_type, s1_value = getAttributes(instruction[2])
            s2_type, s2_value = getAttributes(instruction[3])
            if (s1_type != "bool" or s2_type != "bool"):
                sys.exit(53)
            value = "false"
            if s1_value == "true" or s2_value == "true":
                value = "true"
            changeVariable(instruction[1], "bool", value)

        elif (instruction[0] == "NOT"):
            type, value = getAttributes(instruction[2])
            if type != "bool":
                sys.exit(53)
            if value == "false":
                changeVariable(instruction[1], "bool", "true")
            else:
                changeVariable(instruction[1], "bool", "false")

        elif (instruction[0] == "INT2CHAR"):
            type, value = getAttributes(instruction[2])
            if type != "int":
                sys.exit(53)
            value = int(value)
            try:
                result = chr(value)
            except:
                sys.exit(58)

            changeVariable(instruction[1], "int", result)

        elif (instruction[0] == "STRI2INT"):
            sym1Type, sym1Value = getAttributes(instruction[2])
            sym2Type, sym2Value = getAttributes(instruction[3])
            if sym1Type != "string" or sym2Type != "int":
                sys.exit(53)
            try:
                result = sym1Value[int(sym2Value)]
                result = ord(result)
            except:
                sys.exit(58)
            changeVariable(instruction[1], "int", result)

        elif (instruction[0] == "READ"):
            instruction[2], value = getAttributes(instruction[2])
            if inputCode is None:
                try:
                    line = input()
                except:
                    line = ""
            else:
                if (Input is None):
                    Input = open(inputCode, 'r')
                line = Input.readline().rstrip()
            if value == "string":
                changeVariable(instruction[1], "string", line)
            elif value == "bool":
                if line.lower() == "true":
                    changeVariable(instruction[1], "bool", "true")
                else:
                    changeVariable(instruction[1], "bool", "false")
            elif value == "int":
                try:
                    changeVariable(instruction[1], "int", str(int(line)))
                except:
                    changeVariable(instruction[1], "int", "0")

        elif (instruction[0] == "WRITE"):
            type, value = getAttributes(instruction[1])
            if type == "nil":
                value = ""
            print(value)

        elif (instruction[0] == "CONCAT"):
            s1_type, s1_value = getAttributes(instruction[2])
            s2_type, s2_value = getAttributes(instruction[3])
            if (s1_type != "string" or s2_type != "string"):
                sys.exit(53)
            try:
                result = s1_value + s2_value
            except:
                sys.exit(58)
            changeVariable(instruction[1], "string", result)

        elif (instruction[0] == "STRLEN"):
            type, value = getAttributes(instruction[2])
            if (type != "string"):
                sys.exit(53)
            changeVariable(instruction[1], "int", len(value))

        elif (instruction[0] == "GETCHAR"):
            getchar(instruction[1], instruction[2], instruction[3])

        elif (instruction[0] == "SETCHAR"):
            setchar(instruction[1], instruction[2], instruction[3])

        elif (instruction[0] == "TYPE"):
            type, value = getAttributes(instruction[2], True)
            if type == None or value == None:
                type = ""
            changeVariable(instruction[1], "string", type)

        elif ((instruction[0] == "LABEL") or (instruction[0] == "JUMP") or (instruction[0] == "JUMPIFEQ") or (instruction[0] == "JUMPIFNEQ") or (instruction[0] == "BREAK") or (instruction[0] == "RETURN") or (instruction[0] == "CALL")):
            continue

        elif (instruction[0] == "EXIT"):
            type, value = getAttributes(instruction[1])
            if type != "int":
                sys.exit(53)
            if int(value) not in range(0, 50):
                sys.exit(57)
            sys.exit(int(value))

        elif (instruction[0] == "DPRINT"):
            type, value = getAttributes(instruction[1], True)
            sys.stderr.write(value)

        else:
            sys.exit(32)


##  Main funkcia programu
##  Skontroluje help a priradí vstupy
def main():
    global inputCode;
    if (len(sys.argv) == 1):
        exit(10)
    elif ("--help" in sys.argv):
        if (len(sys.argv) != 2):
            exit(10)
        printHelp()
    else:
        arguments = parseArguments()
        if ('source' in arguments):
            sourceCode = setFile(arguments["source"])
        if ('input' in arguments):
            inputCode = arguments["input"]
        if ('source' not in arguments):
            sourceCode = loadStdin()
        ## upravy kodu
        checkedDictionary = checkLexical(sourceCode)
        checkedSyntax = checkSyntax(checkedDictionary)
        finalCode = editCode(checkedSyntax)
        codeInterpret(finalCode)
main()