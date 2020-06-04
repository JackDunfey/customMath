import string;
from math import sqrt, cos, pi;
from os import system as cmd;
from flask import Flask, render_template, request;
import sys;
import re;
import json;
dataTable = None;
TT_INT = 'INT'
TT_FLOAT  = 'FLOAT'
TT_NUMBER = (TT_INT,TT_FLOAT);
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_QUOTE = "QUOTE";
TT_POW = 'POW'
TT_FACTO = 'FACTORIAL'
TT_EOF = "EOF"
TT_CONT = "CONT"
TT_EQ = "EQ"
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD = "KEYWORD"
TT_STRING = "STRING"
functions = [
    "sqrt",
    "sin",
    "cos",
    "clear",
    "print"
]
keywords = [
    "VAR"
]
for name in functions:
    keywords.append(name);
dictOfSpecTypes = {
    '+': TT_PLUS,
    '-': TT_MINUS,
    '*': TT_MUL,
    '/': TT_DIV,
    '(': TT_LPAREN,
    ')': TT_RPAREN,
    '^': TT_POW,
    '!': TT_FACTO,
    '=': TT_EQ,
    ';': TT_CONT
}
def clear(): cmd("cls");
def rad(n): return pi*n/180;
DIGITS = "0123456789"
LETTERS = string.ascii_letters
ALPHANUMERIC = LETTERS + DIGITS
CHARACTERS = ALPHANUMERIC+' ._,-/:;\\';
class Token:
    def __init__(self,type,value=None):
        self.type = type;
        self.value = value;
    def __repr__(self):
        if self.value is None:
            return self.type;
        else:
            return f"{self.type}:{self.value}";
class Lexer:
    def __init__(self,fl,fn):
        self.fl = fl;
        self.fn = fn;
        self.idx = -1;
        self.currentChar = None;
        self.advance();
    def advance(self):
        self.idx += 1;
        self.currentChar = self.fl[self.idx] if self.idx < len(self.fl) else None;
    def lex(self):
        tokens = [];
        while self.currentChar != None:
            c = self.currentChar;
            if c in ' \t\n':
                self.advance();
            elif c in dictOfSpecTypes.keys():
                self.advance();
                tokens.append(Token(dictOfSpecTypes[c]));
            elif c in DIGITS:
                tokens.append(self.makeNumberToken());
            elif c == r'"':
                self.advance();
                tokens.append(self.makeStringToken());
            elif c in LETTERS:
                tokens.append(self.makeIdToken());
            else:
                return None, "Invalid Token";
        tokens.append(Token(TT_EOF));
        return tokens, None;
    def makeNumberToken(self):
        num_str = ""
        dp = 0
        while self.currentChar is not None and self.currentChar in DIGITS+'.':
            if self.currentChar == ".":
                if dp == 1:
                    print("Two decimals");
                    sys.exit(1);
                dp = 1;
            num_str += self.currentChar;
            self.advance();
        if dp == 0:
            return Token(TT_INT,int(num_str));
        return Token(TT_FLOAT,float(num_str));
    def makeStringToken(self):
        string = "";
        while self.currentChar is not None and self.currentChar not in '\t\n' and self.currentChar in CHARACTERS:
            string += self.currentChar;
            self.advance();
        if self.currentChar == r'"':
            self.advance();
            return Token(TT_STRING,string);
        else:
            print("ERROR UNTERMINATED STRING");
    def makeIdToken(self):
        string = "";
        while self.currentChar is not None and self.currentChar not in ' \t\n' and self.currentChar in ALPHANUMERIC:
            string += self.currentChar;
            self.advance();
        if string in keywords:
            return Token(TT_KEYWORD,string);
        return Token(TT_IDENTIFIER,string);
########################################
# VALUE NODES
########################################
class StringNode:
    def __init__(self, val_tok):
        self.tok = val_tok;
        self.value = val_tok.value;
    def __repr__(self):
        return f"\"{self.value}\""
class NumberNode:
    def __init__(self,val_tok):
        self.valTok = val_tok;
        self.value = val_tok.value;
    def __repr__(self):
        return f"{self.value}";
########################################
# OPERATION NODES
########################################
class UnaryOpNode:
    def __init__(self,op_tok,numNode):
        self.opTok = op_tok;
        self.node = numNode;
    def __repr__(self):
        return f"({self.opTok},{self.node})";
class BinaryOpNode:
    def __init__(self,left_node,op_tok,right_node):
        self.left = left_node;
        self.right = right_node;
        self.opTok = op_tok;
    def __repr__(self):
        return f"({self.left},{self.opTok},{self.right})";
class PrintNode:
    def __init__(self, node):
        self.node = node;
    def __repr__(self):
        return f"PRINT:{self.node}";
########################################
# VARIABLE NODES
########################################
class VarAssignNode:
    def __init__(self, id_tok, value_node):
        self.tok = id_tok;
        self.value = value_node;
    def __repr__(self):
        return f"({self.tok.value}={self.value})";
class VarAccessNode:
    def __init__(self, id_tok):
        self.tok = id_tok;
    def __repr__(self):
        return f"(get {self.tok.value})";
class Datatable:
    def __init__(self):
        self.map = {};
    def add(self, name, value):
        self.map[name] = value;
    def get(self, name):
        return self.map.get(name, "Variable Not Found");
    def __repr__(self):
        t = [];
        for i in self.map.keys():
            t.append(f"{i}:{self.map[i]}");
        return "\r\n".join(t);
########################################
# OTHER STUFF
########################################
class Parser:
    def __init__(self,tokens):
        self.tokens = tokens;
        self.idx = -1;
        self.currentToken = None;
        self.advance();
    def advance(self):
        self.idx += 1
        self.currentToken = self.tokens[self.idx] if self.idx < len(self.tokens) else None;
    def parse(self,tree=[],tok=None):
        if tok is not None: self.tokens = tok;
        tree.append(self.one());
        if self.currentToken.type not in (TT_EOF,TT_CONT):
            return "Unexpected EOF";
        elif self.currentToken.type == TT_EOF:
            return tree;
        self.advance();
        return self.parse(tree);
    def binopnode(self,left_func,tokens,right_func=None):
        if right_func is None:
            right_func = left_func;
        left = left_func();
        while self.currentToken.type in tokens:
            token = self.currentToken;
            self.advance();
            right = right_func();
            left = BinaryOpNode(left,token,right);
        return left;
    ###########################################
    def one(self):
        if self.currentToken.type == TT_KEYWORD:
            if self.currentToken.value == "VAR":
                self.advance();
                if self.currentToken.type == TT_IDENTIFIER:
                    tok = self.currentToken;
                    self.advance();
                    if self.currentToken.type == TT_EQ:
                        self.advance();
                        return VarAssignNode(tok,self.one());
            elif self.currentToken.value == "print":
                self.advance();
                if self.currentToken.type ==  TT_LPAREN:
                    self.advance();
                    expr = self.one();
                    if self.currentToken.type == TT_RPAREN:
                        self.advance();
                        return PrintNode(expr);
        return self.binopnode(self.two,(TT_PLUS,TT_MINUS));
    def two(self):
        return self.binopnode(self.three,(TT_MUL,TT_DIV));
    def three(self):
        tok = self.currentToken;
        while tok.type in (TT_PLUS, TT_MINUS):
            self.advance();
            factor = self.three();
            return UnaryOpNode(tok,factor);
        global functions;
        if tok.type == TT_KEYWORD and tok.value in functions:
            self.advance();
            if self.currentToken.type == TT_LPAREN:
                self.advance();
                expr = self.one();
                if self.currentToken.type == TT_RPAREN:
                    self.advance()
                    return UnaryOpNode(tok,expr);
        return self.four();
    def four(self):
        return self.binopnode(self.five,(TT_POW,),self.three);
    def five(self):
        node = self.six();
        tok = self.currentToken;
        while tok.type in (TT_FACTO,):
            self.advance();
            node = UnaryOpNode(tok,node);
            tok = self.currentToken;
        return node;
    def six(self):
        tok = self.currentToken;
        if tok.type in TT_NUMBER:
            self.advance();
            return NumberNode(tok);
        elif tok.type == TT_LPAREN:
            self.advance();
            expr = self.one();
            if self.currentToken.type == TT_RPAREN:
                self.advance();
                return expr;
            else:
                print("Error no right parenthesis found");
        elif tok.type == TT_STRING:
            self.advance();
            return StringNode(tok);
        elif tok.type == TT_IDENTIFIER:
            self.advance();
            return VarAccessNode(tok);
    ##############################
    def __repr__(self):
        return f"{self.tokens}";
class Interpreter:
    def __init__(self, source, script):
        self.source = source;
        self.rootNode = script;
        self.displayOutput = [];
    def interpret(self):
        return self.visit(self.rootNode);
    def visit(self,node):
        return getattr(self,f"visit_{type(node).__name__}",self.no_visit_method)(node);
    def no_visit_method(self,node):
        print(f"No visit method defined for node of type {type(node).__name__}");
        return None;
    ########################################
    def visit_NumberNode(self,node):
        return Number(node.value);
    def visit_StringNode(self,node):
        return String(node.value);
    ########################################
    def visit_UnaryOpNode(self,node):
        operator = node.opTok;
        number = self.visit(node.node);
        if operator.type == TT_MINUS:
            return number.mulWith(Number(-1));
        elif operator.type == TT_FACTO:
            return number.factorial();
        elif operator.type == TT_PLUS:
            return number;
        ####
        elif operator.type == TT_KEYWORD:
            if operator.value == "clear":
                cmd("cls");
                return None;
            else:
                return getattr(number,operator.value,number.invalid_method)();
    def visit_BinaryOpNode(self,node):
        operator = node.opTok;
        left = self.visit(node.left);
        right = self.visit(node.right);
        if operator.type == TT_PLUS:
            return left.add(right);
        elif operator.type == TT_MINUS:
            return left.subtract(right);
        elif operator.type == TT_MUL:
            return left.multiply(right);
        elif operator.type == TT_DIV:
            return left.divide(right);
        elif operator.type == TT_POW:
            return left.pow(right);
    ########################################
    def visit_VarAssignNode(self,node):
        global dataTable;
        dataTable.add(node.tok.value,self.visit(node.value));
        return node;
    def visit_VarAccessNode(self,node):
        global dataTable;
        return dataTable.get(node.tok.value);
    ########################################
    def visit_PrintNode(self,node):
        self.displayOutput.append(self.visit(node.node));
class Simplifier:
    def __init__(self,ast):
        self.ast = ast;
    def simplify(self,ast=None):
        if ast is not None:
            self.ast = ast;
        if type(ast).__name__ == "BinaryOpNode":
            while type(ast.left).__name__ != "IdNode" and type(ast.right).__name__ != "IdNode":
                self.do_upadte();
    def update(self):
        return getattr(self,f"update_{type(self.ast).__name__}","no_update_method")(self.ast);
    def no_update_method(self,node):
        return f"No simplification method found for node of type {type(node).__name__}";
    #############################
    def update_BinaryOpNode(self,node):
        left_invalid = type(node.left).__name__ in (TT_IDENTIFIER,);
        right_invalid = type(node.right).__name__ in (TT_IDENTIFIER,);
        if left_invalid and right_invalid:
            return node;
        elif left_invalid:
            return BinaryOpNode(node.left,node.opTok,self.update(node.right));
        elif right_invalid:
            return BinaryOpNode(self.update(node.left),node.opTok,node.right);
########################################
# VALUES
########################################
class Number:
    def __init__(self,value):
        self.value = value;
    #Binary
    def add(self,other):
        if isinstance(other,Number):
            return Number(self.value+other.value);
    def subtract(self,other):
        if isinstance(other,Number):
            return Number(self.value-other.value);
    def multiply(self,other):
        if isinstance(other,Number):
            return Number(self.value*other.value);
    def divide(self,other):
        if isinstance(other,Number):
            return Number(self.value/other.value);
    def pow(self,other):
        if isinstance(other,Number):
            return Number(self.value**other.value);
    #Unary
    def factorial(self):
        nVal = 1;
        for i in range(self.value):
            nVal *= i+1;
        return Number(nVal);
    def sqrt(self):
        return Number(sqrt(self.value));
    def cos(self):
        global mode;
        if mode == "RAD":
            return Number(cos(self.value));
        else:
            return Number(cos(rad(self.value)));
    ########################################
    def invalid_method(self):
        print("Invalid method being applied to number");
        return None;
    def __repr__(self):
        return f"{self.value}";
class String:
    def __init__(self, value):
        self.value = value;
    def add(self, other):
        if isinstance(other, String):
            return String(self.value+other.value);
        else:
            return String(self.value+str(other.value));
    def multiply(self, other):
        if isinstance(other, Number):
            return String(self.value*other.value);
    def __repr__(self):
        return f"{self.value}";
########################################
# RUNNING
########################################
def debug(fn, fl):
    global dataTable;
    if not dataTable:
        dataTable = Datatable();
    print(fl);
    #Make '|' equal to TT_EOF but keep looping until TT_EOF is reached
    lexer = Lexer(fl, fn);
    tokens, error = lexer.lex();
    if error:
        print(f"Error: {error}");
    else:
        print(f"Token: {tokens}");
    parser = Parser(tokens);
    ast = parser.parse([]);
    print(ast);
    out = [];
    output = [];
    for tree in ast:
        if tree is None: continue;
        interpreter = Interpreter(fn,tree);
        out.append(interpreter.interpret());
        output += interpreter.displayOutput;
    print("Datatable:",dataTable);
    if len(output)>0: return "\n".join([str(vl) for vl in output]);
def console(fn,fl):
    global dataTable;
    if not dataTable:
        dataTable = Datatable();
    lexer = Lexer(fl, fn);
    tokens, error = lexer.lex();
    parser = Parser(tokens);
    ast = parser.parse([]);
    out = [];
    output = [];
    for tree in ast:
        if tree is None: continue;
        interpreter = Interpreter(fn,tree);
        out.append(interpreter.interpret());
        output += interpreter.displayOutput;
    if len(output)>0: print("\n".join([str(vl) for vl in output]));
def run(fn, fl):
    global dataTable;
    if not dataTable:
        dataTable = Datatable();
    tokens, error = Lexer(fl, fn).lex();
    if error: print(f"Error: {error}");
    ast = Parser(tokens).parse([]);
    out = [];
    output = [];
    for tree in ast:
        if tree is None: continue;
        interpreter = Interpreter(fn,tree);
        out.append(interpreter.interpret());
        output += interpreter.displayOutput;
    if len(output)>0: return "\n".join([str(vl) for vl in output]);
def readFile(filename):
    return open(filename,'r').read();
app = Flask("app");
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        global dataTable;
        dataTable = None;
        return json.dumps({"body":debug("website",request.json)});
    return render_template("index.html");
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1].split(r".")[1] != "cusm":
            print("Invalid file type");
            sys.exit(1);
        console(sys.argv[1],readFile(sys.argv[1]))
    else:
        app.run(port=80, host="127.0.0.1", debug=True);
