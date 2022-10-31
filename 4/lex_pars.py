"""
This file contains the implementation of the Lexer and Parser classes used by the Reader class in bx2ast.py
It makes extensive use of the PLY library in order to convert symbols into tokens, and then parse these tokens to generate the AST corresponding to a specific BX program. 
"""
import ply.lex as lex 
import ply.yacc as yacc
import AST as ast

"""
Part A of the file: Source & Sloc 
In order to better keep track of error messages and their location (line and column numbers) we create two classes. 
Source: object that holds two attributes: 
        -> provenance: name of source code file 
        -> data: source code string representation
It will be given as an argument to the Lexer and then passed on to every Sloc instance. 

Sloc: object that holds three attributes: 
        -> source: Source object as described above 
        -> lineno: line number
        -> lexpos: position of the lexer
A Sloc object is given as an input argument to every Node of the AST classes. This will be usefull when detecting errors after the Lexing & Parsing. 
We will use the Sloc class to displat the error messages. 
"""
# ================================================================================
class Source:
    def __init__(self, provenance: str, data: str):
        self.provenance = provenance
        self.data = data
    
class Sloc:
    severity_map = ('Debug ', 'Info ', 'Warning ', "ERROR ")

    def __init__(self, source: Source, lineno: int, lexpos: int):
        self.source = source 
        self.lineno = lineno
        self.lexpos = lexpos
    
    def print_error_message(self, msg: str, severity=1, err=None):
        """
        Base error message function. This function will either be directly called to handle lexing errors or called by the parsing errors function. 
        """
        if err is(None): print("HELLPPPP")
        err_msg = ''
        if self.source is not None:
            eol = self.source.data.rfind('\n', 0, self.lexpos)
            colno = self.lexpos - eol
            err_msg = f'\n{self.source.data}\nLine:{self.lineno}.Column:{colno}:\n'
        severity = max(0, min(4, severity))
        err_msg += Sloc.severity_map[severity] + msg
        print(err_msg)
        if err: err

# ================================================================================
"""
Part B of the file: Lexer
Using some documentation found online: https://www.dabeaz.com/ply/ply.html we encapsulates the lexer in 
our own Lexer class. This is easier in order to manage the different parts of the program.
"""
# ================================================================================

class Lexer:
    def __init__(self, provenance: str, data: str):
        """
        Initialisation of the lexer object (from ply library).
        """
        self.source = Source(provenance, data)
        self.data = data 
        self.lexer = lex.lex(module=self)
        self.lexer.input(self.data)
        self.iseof = False 

    # =============== PLY used variables ==================

    # Key words of the BX grammar 
    reserved = {
        'var': "VAR", 
        'int': 'INT', 
        'def': "DEF",
        'main': "MAIN", 
        'print': "PRINT",
        'if': 'IF', 
        'else': 'ELSE', 
        'while': 'WHILE', 
        'break': 'BREAK', 
        'continue': 'CONTINUE', 
        'true': 'TRUE', 
        'false': 'FALSE'
    }

    # Tokens of the BX grammar
    tokens = ('PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULUS', 
    'BIT_OR', 'BIT_AND', 'BIT_XOR', 'BIT_LSHIFT', 'BIT_RSHIFT', 'BIT_NEGATION', 
    'EQ', 'NEQ', 'LT', 'LTEQ', 'GT', 'GTEQ',
    'AND', 'OR', 'NOT',
    'IDENT', 'NUMBER', 
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET','SEMICOLON', 'COLON', 'EOF',
    'ASSIGN') + tuple(reserved.values())

    # =============== Associating PLY tokens and symobls ==================

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MODULUS = r'%'

    t_BIT_OR = r'\|'
    t_BIT_AND = r'&'
    t_BIT_XOR = r'\^'
    t_BIT_LSHIFT = r'<<'
    t_BIT_RSHIFT = r'>>'
    t_BIT_NEGATION = r'~'
    
    t_EQ = r'=='
    t_NEQ = r'!='
    t_LT = r'<'
    t_LTEQ = r'<='
    t_GT = r'>'
    t_GTEQ = r'>='

    t_AND = r'&&'
    t_OR = r'\|\|'
    t_NOT = r'!'
    
    t_LPAREN = r'\('
    t_LBRACKET = r'{'
    t_RBRACKET = r'}'
    t_RPAREN = r'\)'
    t_SEMICOLON = r';'
    t_COLON = r':'

    t_ASSIGN = r'='

    # ============= PLY token processing code ================

    def t_IDENT(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = Lexer.reserved.get(t.value, 'IDENT')
        return t 

    def t_NUMBER(self, t):
        r'0|[1-9][0-9]*'
        t.value = int(t.value)
        if not (-9223372036854775808 <= t.value < 9223372036854775808):
            msg = f'Number value {t.value} out supported range [-2^63, 2^63)'
            Sloc(self.source, t.lineno, t.lexpos).print_error_message(msg, 3, err=SyntaxError)
        return t
    
    def t_eof(self, t):
        if not self.iseof:
            self.iseof = True 
            t.type = 'EOF'
            return t

    def t_error(self, t):
        if not t:
            return 
        msg = f"Illegal character ’{t.value[0]}’"
        Sloc(self.source, t.lineno, t.lexpos).print_error_message(msg, 3, err=SyntaxError)
        t.lexer.skip(1)

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    def t_whitespace(self, t): 
        r'//.*\n'
        if t.value[-1] == '\n': 
            t.lexer.lineno+=1

    def t_COMMENT(self, t):
        r'//.*'
        t.lexer.lineno += 1
        pass

    t_ignore = ' \t\f\v'

# ============== Error Handling =======================

    # def position(self, t):
    #     line_start = self.data.rfind('\n', 0, t.lexpos) + 1
    #     return f'line:{t.lineno}, col:{t.lexpos - line_start + 1}'

    # def error_message(self, t, msg):
    #     print(f'{self.position(t)}: Error:{msg}')
    #     msg = f'{self.position(t)}: Error:{msg}'
    #     raise SyntaxError(msg)

# ================================================================================

"""
Part C of the file: Parser
Similar to the Lexer, we encapsulate the PLY parser in our own Parser class
in order to better manage which part of the program is acting on what input.
"""

class Parser: 
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.parser = yacc.yacc(module=self, start='program')

    def sloc(self, p, n: int):
        """
        Useful function to create sloc instances every time we create the AST instance corresponding to the parsed code.
        """
        return Sloc(self.lexer.source, p.lineno(n), p.lexpos(n))

    def parse(self):
        """
        Encapsulating the ply parser parse function in our own parse function. 
        """
        return self.parser.parse(lexer=self.lexer.lexer)

    # =========== PLY used variables ======================

    tokens = Lexer.tokens + ('UMINUS',) #Adding UMINUS token to handle expressions of the form: y = -x. 

    # Precedence table to be used when parsing expression containing unary/binary operations (work done by the PLY library)
    precedence = (
        ('left', 'OR'), 
        ('left', 'AND'), 
        ('left', 'BIT_OR'),
        ('left', 'BIT_XOR'),
        ('left', 'BIT_AND'),
        ('nonassoc', 'EQ', 'NEQ'), 
        ('nonassoc', 'LT', 'LTEQ', 'GT', 'GTEQ'), 
        ('left', 'BIT_LSHIFT', 'BIT_RSHIFT'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE', 'MODULUS'),
        ('left', 'UMINUS', 'NOT'),
        ('left', 'BIT_NEGATION'),
    )

    # ================== Expressions ======================

    def p_expr_ident(self, p):
        #  p[0]   p[1]
        """expr : IDENT"""
        p[0] = ast.ExpressionVar(self.sloc(p, 1), p[1], "int")

    def p_expr_number(self, p):
        #  p[0]   p[1]
        """expr : NUMBER"""
        p[0] = ast.ExpressionInt(self.sloc(p, 1), int(p[1]))

    def p_expr_boolean(self, p):
        #  p[0]  p[1]
        """expr : TRUE
                | FALSE """
        p[0] = ast.Bool(self.sloc(p, 1), (p[1] == 'true'))

    def p_expr_uniop(self, p):
        #  p[0]   p[1]        p[2]
        """expr : BIT_NEGATION expr
                | MINUS expr %prec UMINUS
                | UMINUS expr
                | NOT expr
        """
        if p[1] == '-': #Handling the UMINUS
            p[1] = '-.'
        p[0] = ast.ExpressionUniOp(self.sloc(p, 1), p[1], p[2])

    def p_expr_binop(self, p):
        #  p[0]   p[1] p[2] p[3] 
        """expr : expr PLUS expr
                | expr MINUS expr
                | expr TIMES expr
                | expr DIVIDE expr
                | expr MODULUS expr
                | expr BIT_OR expr
                | expr BIT_AND expr 
                | expr BIT_XOR expr
                | expr BIT_LSHIFT expr 
                | expr BIT_RSHIFT expr
                | expr EQ expr 
                | expr NEQ expr
                | expr LT expr 
                | expr LTEQ expr 
                | expr GT expr 
                | expr GTEQ expr 
                | expr AND expr 
                | expr OR expr
        """
        p[0] = ast.ExpressionBinOp(self.sloc(p, 1), p[2], p[1], p[3])


    def p_expr_parens(self, p):
        #  p[0]   p[1]   p[2] p[3] 
        """expr : LPAREN expr RPAREN"""
        p[0] = p[2]

    # ================== Statements =======================

    def p_stmt(self, p):
        #   p[0]    p[1]  p[2]
        """ stmts : stmts stmt 
                    |"""
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]
            p[1].append(p[2])
    
    def p_stmt_decl(self, p):
        #  p[0]    p[1] p[2]  p[3]  p[4] p[5]  p[6] p[7]
        """ stmt : VAR IDENT ASSIGN expr COLON INT SEMICOLON"""
        p[0] = ast.Vardecl(
            self.sloc(p, 1), 
            ast.ExpressionVar(self.sloc(p, 2), p[2], p[6]),
            p[4],
            p[6])

    def p_stmt_block(self, p):
        #  p[0]   p[1]
        """stmt : block"""
        p[0] = p[1]

    def p_block(self, p):
        #  p[0]     p[1]    p[2]  p[3]
        """block : LBRACKET stmts RBRACKET"""
        p[0] = ast.Block(self.sloc(p, 1), p[2])

    def p_stmt_assign(self, p):
        #  p[0]     p[1] p[2] p[3] p[4]
        """ stmt : IDENT ASSIGN expr SEMICOLON"""
        p[0] = ast.Assign(
            self.sloc(p, 1),
            ast.ExpressionVar(self.sloc(p, 1), p[1], "int"), 
            p[3])

    def p_stmt_print(self, p):
        #   p[0]   p[1]  p[2]   p[3] p[4]   p[5]
        """ stmt : PRINT LPAREN expr RPAREN SEMICOLON"""
        p[0] = ast.Print(self.sloc(p, 1), p[3])

    def p_stmt_ifelse(self, p):
        #   p[0]    p[1]
        """ stmt : ifelse"""
        p[0] = p[1]

    def p_stmt_ifrest(self, p):
        #   p[0]    p[1] p[2]
        """ifrest : 
                  | ELSE block
                  | ELSE ifelse
        """
        if len(p) == 1:
            p[0] = ast.Block(self.sloc(p, 0), [])
        else:
            p[0] = p[2]
        

    def p_ifelse(self, p):
        #   p[0]    p[1]  p[2] p[3]  p[4]  p[5]  p[6]
        """ ifelse : IF LPAREN expr RPAREN block ifrest"""
        p[0] = ast.IfElse(self.sloc(p, 1), p[3], p[5], p[6])

    def p_stmt_while(self, p):
        #   p[0]    p[1]  p[2]   p[3]   p[4]  p[5] 
        """stmt : WHILE LPAREN expr RPAREN block"""
        p[0] = ast.While(self.sloc(p, 1), p[3], p[5])

    def p_stmt_jump(self, p):
        #  p[0]    p[1]    p[2]
        """stmt : BREAK SEMICOLON
                | CONTINUE SEMICOLON
        """
        p[0] = ast.Jump(self.sloc(p, 1), p[1])

    # ================== Program =======================

    def p_program(self, p):
        # p[0]       p[1] p[2] p[3]  p[4]   p[5]  p[6] 
        """program : DEF MAIN LPAREN RPAREN block EOF"""
        p[0] = ast.Program(self.sloc(p, 1), [], p[5])

    # ================== Error Handling ===================
    def p_error(self, p):
        if not p:
            return 
        msg = f'Syntax error while parsing {p.type}'
        Sloc(self.lexer.source, p.lineno, p.lexpos).print_error_message(msg, 3, err=SyntaxError)

    # def error_message(self, lineno, lexpos, msg):
    #     token = lex.LexToken()
    #     token.lineno = lineno
    #     token.lexpos = lexpos
    #     token.type = None 
    #     token.value = None 
    #     print("token line:", token.lineno)
    #     self.lexer.error_message(token, msg)
