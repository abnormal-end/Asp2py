import re
import os
import sys
from pathlib import Path

class Token():
    KEYWORD = 'K'
    IDENTIFIER = 'I'
    STRING = 'S'
    NUMBER = 'N'
    OPERATOR = 'O'
    PRINTMODE = 'P'
    PRINTINCFILE = 'F'

    def __init__(self, name, type, value, line, column):
        self.name = name.strip().lower()
        self.type = type
        self.value = value
        self.line = line + 1
        self.column = column + 1
    
    def __str__(self):
        if self.value:
            return f"[{self.type}|{self.name}={self.value}] "
        return f"[{self.type}|{self.name}] "
    
class Lexer():
    reserved = [ "if","then","else","elseif","end","end if","dim","function","end function","do while","loop","for","next","exit for",
                 "exit do","exit function", "mod","and","or","not","set","on error resume next","call","byref","byval","new"]
    reserved_print = [ "#include file", "#include virtual" ]
    double_operators = [ "==", "!=", ">=", "<=" ]
    start_identifier = re.compile('[a-zA-Z_]')
    in_identifier = re.compile('[a-zA-Z0-9_]')
    start_in_operator = re.compile('[\-+/*\(\)=><\.,]') 
    start_string = re.compile('\"')
    start_number = re.compile('[0-9]')
    in_number = re.compile('[0-9\.]')
    print_inc = re.compile(' ?#include +(\w+)[^"]*"([^"]+) ?"')

    def __init__(self):
        self.source_tokens = []
        self.errors = []
        self.in_asp = False

    def lex(self, source):
        self.l = 0 # line number
        self.i = 0 # position in that line
        self.start_l = self.l
        self.start_i = self.i
        self.source = source

        while self.l < len(source):
            line = source[self.l]
            self.tokens = []
            self.i = 0
            while self.i < len(line):
                char = self.get_char()
                char2 = self.get_char(1)
                char3 = self.get_char(2)
                self.start_l = self.l
                self.start_i = self.i

                if self.in_asp:
                    if char == '%' and char2 == '>':
                        self.in_asp = False
                        self.i += 2
                    elif char == '\'' or (char == 'R' and char2 == 'E' and char3 == 'M'):
                        break
                    elif Lexer.start_identifier.match(char):
                        self.parse_identifier(source)
                    elif Lexer.start_in_operator.match(char):
                        self.parse_operator(source)
                    elif Lexer.start_string.match(char):
                        self.parse_string(source)
                    elif Lexer.start_number.match(char):
                        self.parse_number(source)
                    else:
                        self.i += 1
                else:
                    self.parse_print(source)

            self.source_tokens.append(self.tokens)
            self.l += 1
        self.set_type()
    
    def get_char(self, add = 0):
        return self.source[self.l][self.i + add] if self.l < len(self.source) and self.i + add < len(self.source[self.l]) else '\n'
    
    def parse_identifier(self, source):
        acc = ""
        while self.i < len(source[self.l]):
            char = self.get_char()
            if not Lexer.in_identifier.match(char):
                break
            acc += char
            self.i += 1
        self.tokens.append(Token(acc, Token.IDENTIFIER, None, self.start_l, self.start_i))
    
    def parse_operator(self, source):
        acc = ""
        while self.i < len(source[self.l]):
            char = self.get_char()
            if not Lexer.start_in_operator.match(char):
                break
            acc += char
            self.i += 1
        if len(acc) > 1 and acc in Lexer.double_operators:
            self.tokens.append(Token(acc, Token.OPERATOR, None, self.start_l, self.start_i))
        else:
            for i, op in enumerate(acc):
                self.tokens.append(Token(op, Token.OPERATOR, None, self.start_l, self.start_i + i))

    def parse_string(self, source):
        acc = ""
        self.i += 1
        while self.i < len(source[self.l]):
            char = self.get_char()
            char2 = self.get_char(1)

            if char == '"':
                if char2 == '"':
                    acc += char
                    self.i += 1
                else:
                    self.tokens.append(Token("#", Token.STRING, acc, self.start_l, self.start_i))
                    self.i += 1
                    return
            elif char != "\n":
                acc += char
            self.i += 1
        self.set_error(f"Missing string closing: {acc}", self.l, self.i)

    def parse_number(self, source):
        acc = ""
        while self.i < len(source[self.l]):
            char = self.get_char()
            if not Lexer.in_number.match(char):
                break
            acc += char
            self.i += 1
        self.tokens.append(Token(acc, Token.NUMBER, None, self.start_l, self.start_i))
    
    def parse_print(self, source):
        acc = ""
        while self.l < len(source):
            while self.i < len(source[self.l]):
                char = self.get_char()

                if char == '<' and self.get_char(1) == '%':
                    return self.parse_print_add_token(acc)
                elif char == '<' and self.get_char(1) == '!' and self.get_char(2) == '-' and self.get_char(3) == '-':
                    self.parse_print_add_token(acc, False)
                    acc = ""
                    self.parse_print_command(source)
                else:
                    acc += char
                    self.i += 1
            self.l += 1
            self.i = 0
        self.parse_print_add_token(acc)
    
    def parse_print_add_token(self, acc, in_asp = True):
        if len(acc) > 0:
            self.tokens.append(Token("#", Token.PRINTMODE, acc, self.start_l, self.start_i))
        self.i += 2
        self.in_asp = in_asp

    def parse_print_command(self, source):
        acc = ""
        self.i += 2
        while self.i < len(source[self.l]):
            char = self.get_char()
            if char == '-' and self.get_char(1) == '-' and self.get_char(2) == '>':
                match = Lexer.print_inc.match(acc)
                if match:
                    self.tokens.append(Token(match[1], Token.PRINTINCFILE, match[2], self.start_l, self.start_i))
                else:
                    self.set_error(f"Invalid command content: {acc}", self.l, self.i)
                self.i += 3
                return
            elif char != "\n":
                acc += char
            self.i += 1
        self.set_error(f"Invalid command closing: {acc}", self.l, self.i)
    
    def set_type(self):
        for l in range(0, len(self.source_tokens)):
            for i in range(0, len(self.source_tokens[l])):
                token = self.source_tokens[l][i]
                if i + 1 < len(self.source_tokens[l]):
                    token2 = self.source_tokens[l][i + 1]
                    merged = token.name + " " + token2.name
                    if merged in Lexer.reserved:
                        token.name = merged
                        token.type = Token.KEYWORD
                        token2.name = ""
                        continue
                if token.name in Lexer.reserved:
                    token.type = Token.KEYWORD
            self.source_tokens[l] = [t for t in self.source_tokens[l] if t.name != ""]

    def set_error(self, errormessage, line, column):
        ln = ""
        if line >= 0:
            ln = f"Line {line + 1}"
            if column >= 0:
                ln += f", column {column + 1}"
            ln += ": "
        self.errors.append(ln + errormessage)

    def print(self):
        for line in lexer.source_tokens:
            for t in line:
                print(t, end="")
            print("")
    
    def print_errors(self):
        if len(self.errors) > 0:
            print("\n/!\\ Lexing error(s) detected:\n")
        for err in self.errors:
            print(err, file=sys.stderr)
 
def to_array(string):
    if string is None:
        return None
    else:
        string = string if isinstance(string, list) else [ string ]
    return string

class Branch():
    def __init__(self, token, line, started):
        self.scope = {}
        self.token = token
        self.line = line
        self.started = started

class BranchControl():
    def __init__(self, stop_branch = False, create_branch = False, create_started_branch = False, parent_token_names = None, start_parent = False):
        self.scope = {}
        self.stop_branch = stop_branch
        self.create_branch = create_branch or create_started_branch
        self.create_started_branch = create_started_branch
        self.start_parent = start_parent
        self.parent_token_names = to_array(parent_token_names)

class LinkedInst():
    def __init__(self, token_type = None, allowed_list = None, is_end = False, set_name = False, set_value = False):
        self.token_type = token_type
        self.any = allowed_list is None
        self.allowed_list = to_array(allowed_list)
        self.is_end = is_end
        self.set_name = set_name
        self.set_value = set_value
        self.nexts = []

    def add_next(self, next):
        self.nexts.append(next)

    def get_next(self, token, instruction):
        result = self._get_next(token)
        if result and (result.set_name or result.set_value):
            if instruction.line is None:
                instruction.line = token.line 
            if result.set_name:
                instruction.name = token.name
            if result.set_value:
                instruction.value = token.value 
        return result

    def _get_next(self, token):
        for elem in self.nexts:
            if token.type == elem.token_type:
                if elem.any:
                    return elem
                if token.name in elem.allowed_list:
                    return elem
        return None

class InstructionRules():
    def __init__(self):
        self.rules = {}
        self.rules["function"] = self._get_rule_function()
    
    def identify(self, tokens):
        if len(tokens) > 0 and tokens[0].name == "function":
            return self.rules["function"]

    def _get_rule_function(self):
        function = LinkedInst("function")

        function_name_idenfier = LinkedInst(Token.IDENTIFIER, set_name = True)
        function.add_next(function_name_idenfier)

        left_parenthesis = LinkedInst(Token.OPERATOR, "(")
        function_name_idenfier.add_next(left_parenthesis)

        by = LinkedInst(Token.KEYWORD, ["byval", "byref"])
        left_parenthesis.add_next(by)

        idenfier = LinkedInst(Token.IDENTIFIER)
        left_parenthesis.add_next(idenfier)# byval/byref optional
        by.add_next(idenfier)
        
        comma = LinkedInst(Token.OPERATOR, ",")
        idenfier.add_next(comma)
        comma.add_next(by) # byval/byref optional
        comma.add_next(idenfier)

        right_parenthesis = LinkedInst(Token.OPERATOR, ")", is_end = True)
        idenfier.add_next(right_parenthesis)
        left_parenthesis.add_next(right_parenthesis) # args optional

        return function

class Instruction():
     def __init__(self):
        self.line = None
        self.name = None
        self.value = None

class Parser():
    branch_controls = {
        "if": BranchControl(create_branch = True),
        "then": BranchControl(parent_token_names = ["if", "elseif"], start_parent = True),
        "elseif": BranchControl(stop_branch = True, create_branch = True, parent_token_names = ["if", "elseif"]),
        "else": BranchControl(stop_branch = True, create_started_branch = True, parent_token_names = ["if", "elseif"]),
        "end if": BranchControl(stop_branch = True, parent_token_names = ["if", "else", "elseif"]),
        "for each": BranchControl(create_started_branch = True),
        "next": BranchControl(stop_branch = True, parent_token_names = "for each"),
        "do while": BranchControl(create_started_branch = True),
        "loop": BranchControl(stop_branch = True, parent_token_names = "do while"),
        "function": BranchControl(create_started_branch = True, parent_token_names = ""),
        "end function": BranchControl(stop_branch = True, parent_token_names = "function"),
        "sub": BranchControl(create_started_branch = True, parent_token_names = ""),
        "end sub": BranchControl(stop_branch = True, parent_token_names = "function"),
    }
    instruction_rules = InstructionRules()

    def __init__(self):
        self.errors = []
        self.identified = {}
    
    def parse(self, tokens):
        open_branches = []
        current_branch = None
        for i, tokens_row in enumerate(tokens):
            for j, token in enumerate(tokens_row):
                current_branch = open_branches[-1] if len(open_branches) > 0 else None
                
                if token.type == Token.KEYWORD:

                    branch_control = Parser.branch_controls.get(token.name)
                    if branch_control:

                        is_parent_in_list = True
                        if branch_control.parent_token_names:
                            if current_branch:
                                is_parent_in_list = current_branch.token.name in branch_control.parent_token_names
                            else:
                                is_parent_in_list = "" in branch_control.parent_token_names

                        if branch_control.stop_branch:
                            if current_branch:
                                if is_parent_in_list:
                                    if current_branch.started:
                                        open_branches.pop()
                                    else:
                                        self.set_error(token, f"not valid for close because parent '{current_branch.token.name}' is not started")
                                        return
                                else:
                                    self.set_error(token, f"not valid for close because parent '{current_branch.token.name}' doesn't allow it")
                                    return
                            else:
                                self.set_error(token, f"not valid for close because no parent found")
                                return
                        
                        if branch_control.start_parent:
                            if current_branch:
                                if is_parent_in_list:
                                    if not current_branch.started:
                                        current_branch.started = True
                                    else:
                                        self.set_error(token, f"not valid for start because parent '{current_branch.token.name}' is already started")
                                        return
                                else:
                                    self.set_error(token, f"not valid for start because parent '{current_branch.token.name}' doesn't allow it")
                                    return
                            else:
                                self.set_error(token, f"not valid for start because no parent found")
                                return
                            
                        if branch_control.create_branch:
                            if is_parent_in_list:
                                if not current_branch or current_branch.started:
                                    open_branches.append(Branch(token, i, branch_control.create_started_branch))
                                else:
                                    self.set_error(token, f"not valid for create because parent '{current_branch.token.name}' not started")
                                    return
                            else:
                                self.set_error(token, f"not valid for create because parent '{current_branch.token.name}' doesn't allow it")
                                return
                    else:
                        if current_branch and not current_branch.started:
                            self.set_error(token, f"wrong position because parent '{current_branch.token.name}' not started")
                            return
                
                elif token.type == Token.IDENTIFIER:
                    references = self.get_identified_dic("#ref")
                    references[token.name] = references.get(token.name, [])
                    references[token.name].append(token)
            
            if len(tokens_row) > 0:
                rule = self.instruction_rules.identify(tokens_row)
                if rule:
                    instruction = Instruction()
                    store = self.get_identified_list(rule.token_type)
                    store.append(instruction)
                    for token in tokens_row[1:]:
                        rule = rule.get_next(token, instruction)
                        if not rule:
                            self.set_error(token, "invalid syntax")
                            return
        if len(open_branches) > 0:
            for branch in open_branches:
                self.set_error(branch.token, f"close missing")
    
    def set_error(self, token, errormessage):
        self.errors.append(f"Line {token.line}, column {token.column }, token '{token.name}': " + errormessage)
    
    def print_errors(self):
        if len(self.errors) > 0:
            print("/!\\ Parsing error(s) detected:\n")
        for err in self.errors:
            print(err, file=sys.stderr)
    
    def get_identified_list(self, name):
        if not name in self.identified:
            self.identified[name] = []
        return self.identified[name]
    
    def get_identified_dic(self, name):
        if not name in self.identified:
            self.identified[name] = {}
        return self.identified[name]

def load_file(file_name):
    with open(os.path.join(str(Path(__file__).parent), file_name), 'r') as file:
        return file.readlines()

if __name__ == "__main__":
    source = load_file("source.asp")
    lexer = Lexer()
    lexer.lex(source)
    #lexer.print()
    lexer.print_errors()

    if len(lexer.errors) == 0:
        parser = Parser()
        parser.parse(lexer.source_tokens)
        parser.print_errors()

        for instruction_type, instruction_list in parser.identified.items():
            if instruction_type[0] == '#':
                print(instruction_type)
                for name, keywords in instruction_list.items():
                    print(f"    {name}")
                    for keyword in keywords:
                        print(f"        {keyword.line}/{keyword.column}")
            else:
                print(instruction_type)
                for instruction in instruction_list:
                    print(f"    {instruction.line}: {instruction.name}" + "" if instruction.value is None else f"={instruction.value}")
