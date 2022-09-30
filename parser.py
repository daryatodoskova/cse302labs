import ply.yacc as yacc
import ply.lex

import bx_ast
import scanner as lexer

class Parser:

    tokens = lexer.Lexer.tokens

    # associativity and precedence groups of operator tokens
    # in the order of increasing precedence
    precedence = (
        ('left', 'BITOR'),
        ('left', 'BITXOR'),
        ('left', 'BITAND'),
        ('left', 'BITSHL', 'BITSHR'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIV', 'MODULUS'),
        ('right', 'UMINUS'),
        ('right', 'BITCOMPL')
        )

    def p_expr_ident(self, p):
        """expr : IDENT"""
        p[0] = bx_ast.ExpressionVar([p.lineno(1), p.lexpos(1)], p[1])

    def p_expr_number(self, p):
        """expr : NUMBER"""
        p[0] = bx_ast.ExpressionInt([p.lineno(1), p.lexpos(1)], p[1])

    def p_expr_binop(self, p):
        """expr : expr PLUS expr
                | expr MINUS expr
                | expr TIMES expr
                | expr DIV expr
                | expr MODULUS expr
                | expr BITAND expr
                | expr BITOR expr
                | expr BITXOR expr
                | expr BITSHL expr
                | expr BITSHR expr"""
        p[0] = bx_ast.ExpressionBinOp([p.lineno(1), p.lexpos(1)], p[2], p[1], p[3])

    def p_expr_uniop(self, p):
      """expr : MINUS expr %prec UMINUS
              | UMINUS expr
              | BITCOMPL expr"""
      # %prec UMINUS overrides the default rule precedence
      if p[1] == '-':
          p[1] = '-.' #for UMINUS
      p[0] = bx_ast.ExpressionUniOp([p.lineno(1), p.lexpos(1)], p[1], p[2])

    def p_expr_parens(self, p):
        """expr : LPAREN expr LPAREN"""
        p[0] = p[2]

    def p_stmt_assign(self, p):
        """stmt : IDENT EQ expr SEMICOLON"""
        p[0] = bx_ast.Assign([p.lineno(1), p.lexpos(1)],
                      bx_ast.ExpressionVar([p.lineno(1), p.lexpos(1)], p[1]), p[3])

    def p_stmt_print(self, p):
        """stmt : PRINT LPAREN expr RPAREN SEMICOLON"""
        p[0] = bx_ast.Print([p.lineno(1), p.lexpos(1)], p[3])

    def p_stmt_vardecl(self, p):
        """stmt : VAR IDENT EQ expr COLON INT SEMICOLON"""
        p[0] = bx_ast.Vardecl([p.lineno(1), p.lexpos(1)], bx_ast.ExpressionVar([p.lineno(2), p.lexpos(2)], p[2]), p[4])

    def p_stmts(self, p):
      """stmts : stmts stmt
               | """
      if len(p) == 1:   # empty case
        p[0] = []
      else:             # nonempty case
        p[0] = p[1]
        p[1].append(p[2])

    def p_program(self, p):
        """program : DEF MAIN LPAREN RPAREN LBRACE stmts RBRACE EOF"""
        p[0] = bx_ast.Program([p.lineno(1), p.lexpos(1)], p[6])

    # detect parse errors in the token stream.
    def p_error(self, p):
        if p is None:
            print(f"Syntax error in input!")
        p.lexer.lexpos -= len(p.value)
        self.lexer.error(p, f'Syntax error while processing {p.type}')


    def __init__(self, lexer):
        self.lexer = lexer
        self.parser = yacc.yacc(module=self, start='program')

    def error(self, lineno, lexpos, msg):
      token = ply.lex.LexToken()
      token.lineno = lineno
      token.lexpos = lexpos
      token.type = None
      token.value = None
      self.lexer.error(token, msg)

    def parse(self):
      return self.parser.parse(lexer=self.lexer.lexer, tracking=True)


import json
import sys

from bx_ast import Program
from scanner import Lexer

def load_bx(fn):
  assert fn.endswith('.bx')
  with open(fn, 'r') as fp:
    data = fp.read()
    lexer = Lexer(data, fn)
    parser = Parser(lexer)
    prog = parser.parse()
    assert prog is not None
    prog.syntax_check(parser.error)
    return prog

# main function from lex.py to tokenize from standard input
# or from file specified on command line
if __name__ == '__main__':
  from pathlib import Path

  def test(fn):
    fn = str(fn)
    print(f'-- {str(fn)} --')
    try:
      print(load_bx(fn).js_obj)
    except SyntaxError: pass
