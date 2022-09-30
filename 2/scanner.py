import ply.lex as lex


class Lexer:

    def __init__(self, data, provenance):
        self.provenance = provenance
        self.data = data
        self.lexer = lex.lex(module=self)
        # Reset the lexer and store a new input string.
        self.lexer.input(self.data)
        self.iseof = False


    reserved = {
                'print': 'PRINT',
                'main': 'MAIN',
                'def': 'DEF',
                'var': 'VAR',
                'int': 'INT'
                }

    # all possible token names that can be produced by the lexer
    tokens = ('PLUS',
                'MINUS',
                'UMINUS',
                'TIMES',
                'DIV',
                'MODULUS',
                'BITOR',
                'BITAND',
                'BITXOR',
                'BITSHL',
                'BITSHR',
                'BITCOMPL',
                'EQ',
                'EOF',
                'SEMICOLON',
                'COLON',
                'LPAREN',
                'RPAREN',
                'IDENT',
                'NUMBER',
                'LBRACE',
                'RBRACE') + tuple(reserved.values())

    # Regular expression rules for tokens above
    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    t_PLUS = r'\+'
    t_MINUS = '-'
    t_UMINUS = '-'
    t_TIMES = r'\*'
    t_DIV = r'/'
    t_MODULUS = r'%'
    t_BITOR = r'\|'
    t_BITAND = '&'
    t_BITXOR = r'\^'
    t_BITSHL = '<<'
    t_BITSHR = '>>'
    t_BITCOMPL = '~'

    t_SEMICOLON = ';'
    t_COLON = ':'
    t_EQ = '='
    t_LBRACE = '{'
    t_RBRACE = '}'

    def t_IDENT(self, t):
        r'[A-Za-z_][A-Za-z0-9_]*'
        t.type = Lexer.reserved.get(t.value, 'IDENT')
        return t

    # regexp rule that matches numbers & converts string into int
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        if 0 <= t.value < 9223372036854775808:
            return t
        self.error(t, f'Integer with value {t.value} must be in [0, 2^63)')

    # no return value (token discarded)
    def t_COMMENT(self,t):
        r'//.*\n?'
        pass

    # handle an end-of-file condition in the input
    def t_eof(self, t):
      if not self.iseof:
        self.iseof = True
        t.type = 'EOF'
        return t

    # compute column
    def find_column(self, t):
      line_start = self.data.rfind('\n', 0, t.lexpos) + 1
      return f'{self.provenance}:{t.lineno}.{t.lexpos - line_start + 1}'

    def error(self, t, msg):
      print(f'{self.find_column(t)}:Error:{msg}')
      raise SyntaxError(msg)

    # handleillegalcharactersintheinput.
    def t_error(self, t):
        self.error(t, f"Illegal character '{t.value[0]}'")

    # rule to track line numbers
    def t_newline(self, t):
        r'\n'
        t.lexer.lineno += 1

    def t_whitespace(self, t):
      r'//.*\n?'
      if t.value[-1] == '\n':
        t.lexer.lineno += 1
      # returns nothing

    # string containing ignored characters (spaces and tabs)
    t_ignore = ' \t\f\v'
