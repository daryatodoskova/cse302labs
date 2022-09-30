#!/usr/bin/env python3

"""
Darya TODOSKOVA

This is a x64 assembly to TAC pass.

Usage: python3 ast2tac.py astfile.json
Produces: astfile.s (assembly) and astfile.exe (executable)
Requires: a working gcc
"""

import json
import sys
import os
from pathlib import Path

op_codes = {'+': 'add',
            '-': 'sub',
            '*': 'mul',
            '/': 'div',
            '%': 'mod',
            '^': 'xor',
            '|': 'or',
            '&': 'and',
            '~': 'not',
            '-.': 'neg',
            '<<':'shl',
            '>>':'shr'}

#parse tree node
class Node:
  def __init__(self, sloc):
      #source location
      self.sloc = sloc

  def syntax_error(self, msg, errfn):
    if self.sloc is None:
      print('Error:' + msg)
    else:
      #lexpos : index of the token relative to the start of the input text
      lineno, lexpos = self.sloc  #info about the location of the token
      errfn(lineno, lexpos, msg)
    raise SyntaxError(msg)


class Expression(Node):
    def __init__(self, sloc):
        super().__init__(sloc)

    @staticmethod
    def load(js_obj):
        if not isinstance(js_obj, list):
          return None
        if len(js_obj) > 1:
          sloc = js_obj[1]
        else:
          None
        if js_obj[0] == '<expression:var>':
          return ExpressionVar(sloc, js_obj[1]['name'][1]['value'])
        elif js_obj[0] == '<lvalue:var>':
          return ExpressionVar(sloc, js_obj[1]['name'][1]['value'])
        elif js_obj[0] =='<expression:call>':
          return Expression.load(sloc, js_obj[1]['arguments'][0])
        elif js_obj[0] == '<expression:int>':
          return ExpressionInt(sloc, js_obj[1]['value'])
        elif js_obj[0] == '<expression:uniop>':
          operator = js_obj[1]['operator'][1]['value']
          argument = Expression.load(js_obj[1]['argument'])
          return ExpressionUniOp(sloc, operator, argument)
        elif js_obj[0] == '<expression:binop>':
          operator = js_obj[1]['operator'][1]['value']
          left = Expression.load(js_obj[1]['left'])
          right = Expression.load(js_obj[1]['right'])
          return ExpressionBinOp(sloc, operator, left, right)
        else:
          return None


class ExpressionVar(Expression):
    def __init__(self, sloc, name):
      super().__init__(sloc)
      self.name = name

    def syntax_check(self, lvars, errfn):
      # var must already be declared with an earlier vardecl
      if self.name not in lvars:
         self.syntax_error(f'Unknown variable {self.name}', errfn)

    @property
    def js_obj(self):
        return {'tag': 'Variable', 'name': self.name}

class ExpressionInt(Expression):
    def __init__(self, sloc, value):
        super().__init__(sloc)
        self.value = value

    def syntax_check(self, lvars, errfn):
        pass

    @property
    def js_obj(self):
        return {'tag': 'Integer', 'value': str(self.value)}

class ExpressionUniOp(Expression):
    def __init__(self, sloc, operator, argument):
        super().__init__(sloc)
        assert isinstance(operator, str), operator
        self.operator = operator
        self.argument = argument

    def syntax_check(self, lvars, errfn):
        self.argument.syntax_check(lvars, errfn)

    @property
    def js_obj(self):
        return {'tag': 'UniOp',
                'op': self.operator,
                'arg': self.argument}

class ExpressionBinOp(Expression):
    def __init__(self, sloc, operator, left, right):
      super().__init__(sloc)
      assert isinstance(operator, str), operator
      self.operator = operator
      self.left = left
      self.right = right

    def syntax_check(self, lvars, errfn):
      self.left.syntax_check(lvars, errfn)
      self.right.syntax_check(lvars, errfn)

    @property
    def js_obj(self):
      return {'tag': 'BinOp',
              'op': self.operator,
              'larg': self.left,
              'rarg': self.right,
              }




class Statement(Node):
    def __init__(self, sloc):
        super().__init__(sloc)

    @staticmethod
    def load(js_obj):
        if not isinstance(js_obj, list):
            return None
        if len(js_obj) > 1:
            sloc = js_obj[1]
        else:
            sloc = None
        if js_obj[0] == '<statement:assign>':
            return Assign(sloc, Expression.load(js_obj[1]['lvalue']), Expression.load(js_obj[1]['rvalue']))
        elif js_obj[0] == '<statement:eval>':
            js_obj = js_obj[1]['expression']
            return Print(sloc, Expression.load(js_obj))
        else:
            return None

class Vardecl(Statement):

  def __init__(self, sloc, var, init):
    super().__init__(sloc)
    self.var = var
    self.init = init

  def syntax_check(self, lvars, errfn):
    # var must not already be declared
    if self.var.name in lvars:
        self.syntax_error(f'Variable {self.var.name} already declared', errfn)
    # initial value should be syntactically correct
    self.init.syntax_check(lvars, errfn)
    lvars[self.var.name] = self

  @property
  def js_obj(self):
    return {'tag': 'Vardecl',
            'var': self.var.js_obj,
            'init': self.init.js_obj}

class Assign(Statement):
    def __init__(self, sloc, lhs :ExpressionVar, rhs :Expression):
        super().__init__(sloc)
        self.lhs = lhs
        self.rhs = rhs

    def syntax_check(self, lvars, errfn):
        self.lhs.syntax_check(lvars, errfn)
        self.rhs.syntax_check(lvars, errfn)

    @property
    def js_obj(self):
        return {'tag': 'Assign',
        'lhs': self.lhs.js_obj,
        'rhs': self.rhs.js_obj}

class Print(Statement):
    def __init__(self, sloc, arg :Expression):
        super().__init__(sloc)
        assert isinstance(arg, Expression)
        self.arg = arg

    def syntax_check(self, lvars, errfn):
      self.arg.syntax_check(lvars, errfn)

    @property
    def js_obj(self):
        return {'tag': 'Print', 'arg': self.arg.js_obj}




class Program(Node):
  def __init__(self, sloc, stmts):
    super().__init__(sloc)
    self.stmts = stmts


  @staticmethod
  def load(js_obj):
    assert isinstance(js_obj, list)
    if len(js_obj) > 1:
        sloc = js_obj[1]
    else:
        sloc = None
    js_obj = js_obj[0]
    assert len(js_obj) == 2
    js_obj = js_obj[1]
    assert len(js_obj) == 5
    section = js_obj['body'][:]
    stmts = []
    while len(section) > 0:
      stmtt = block.pop(0)
      stmt = Statement.load(stmtt)
      assert stmt is not None, stmtt
      stmts.append(stmt)
    return Program(sloc, stmts)

  def syntax_check(self, errfn):
    lvars = dict()
    for stmt in self.stmts:
      stmt.syntax_check(lvars, errfn)

  @property
  def js_obj(self):
    return {'tag': 'Program',
            'stmts': [stmt.js_obj for stmt in self.stmts]}



class Instruction:
  __slots__ = ['opcode', 'args', 'result']

  def __init__(self, opcode, args, result):
    self.opcode = opcode
    self.args = args
    self.result = result

  @property
  def js_obj(self):
    return {'opcode': self.opcode,
            'args': self.args,
            'result': self.result}


class Programm:
  def __init__(self, program : Program, alg):
    self.localtemporaries = []
    self.instrs = []
    self.__tempdict = dict()
    self.__last = -1
    if alg == 'tmm':
      for stmt in program.stmts:
        self.tmm_stmt(stmt)
    elif alg == 'bmm':
      for stmt in program.stmts:
        self.bmm_stmt(stmt)

  @property
  def js_obj(self):
    return [{'proc': '@main',
             'body': [i.js_obj for i in self.instrs]}]

  def _freshtemp(self):
    self.__last += 1
    t = f'%{self.__last}'
    self.localtemporaries.append(t)
    return t

  def _lookup(self, var):
    t = self.__tempdict.get(var)
    if t is None:
      t = self._freshtemp()
      self.__tempdict[var] = t
    return t

  def _emit(self, opcode, args, result):
    self.instrs.append(Instruction(opcode, args, result))

  def tmm_expr(self, expr, target):
    if isinstance(expr, ExpressionVar):
      self._emit('copy', [self._lookup(expr.name)], target)
    elif isinstance(expr, ExpressionInt):
      self._emit('const', [expr.value], target)
    elif isinstance(expr, ExpressionUniOp):
      arg_target = self._freshtemp()
      self.tmm_expr(expr.argument, arg_target)
      self._emit(op_codes[expr.operator], [arg_target], target)
    elif isinstance(expr, ExpressionBinOp):
      args = []
      arg_target1 = self._freshtemp()
      self.tmm_expr(expr.left, arg_target1)
      args.append(arg_target1)
      arg_target2 = self._freshtemp()
      self.tmm_expr(expr.right, arg_target2)
      args.append(arg_target2)
      self._emit(op_codes[expr.operator], args, target)
    else:
      print(f'In tmm_expr -> unknown expression: {expr.__class__}')


  def tmm_stmt(self, stmt):
    if isinstance(stmt, Vardecl):
      var = self._lookup(stmt.var.name)
      self.tmm_expr(stmt.init, var)
    elif isinstance(stmt, Assign):
      lhss = self._lookup(stmt.lhs.name)
      self.tmm_expr(stmt.rhs, lhss)
    elif isinstance(stmt, Print):
      temp = self._freshtemp()
      self.tmm_expr(stmt.arg, temp)
      self._emit('print', [temp], None)
    else:
      print(f'In tmm_stmt -> unknown statement: {stmt.__class__}')


  def bmm_expr(self, expr):
    if isinstance(expr, ExpressionVar):
      return self._lookup(expr.name)
    elif isinstance(expr, ExpressionInt):
      target = self._freshtemp()
      self._emit('const', [expr.value], target)
      return target
    elif isinstance(expr, ExpressionBinOp):
      args = []
      rarg = self.bmm_expr(expr.right)
      target1 = self._freshtemp()
      self._emit(op_codes[expr.operator], rarg, target1)
      args.append(target1)
      larg = self.bmm_expr(expr.left)
      target2 = self._freshtemp()
      self._emit(op_codes[expr.operator], larg, target2)
      args.append(target2)
      return args
    elif isinstance(expr, ExpressionUniOp):
      arg = self.bmm_expr(expr.argument)
      target = self._freshtemp()
      self._emit(op_codes[expr.operator], arg, target)
      return target
    else:
      print(f'In bmm_expr -> unknown expression: {expr.__class__}')


  def bmm_stmt(self, stmt):
    if isinstance(stmt, Vardecl):
      t_var = self._lookup(stmt.var.name)
      t_init = self.bmm_expr(stmt.init)
      self._emit('copy', [t_init], t_var)
    elif isinstance(stmt, Assign):
      lhss = self._lookup(stmt.lhs.name)
      lhss = self.bmm_expr(stmt.rhs)
      self._emit('copy', [lhss], lhss)
    elif isinstance(stmt, Print):
      temp = self.bmm_expr(stmt.arg)
      self._emit('print', [temp], None)
    else:
      print(f'In bmm_stmt -> unknown statement: {stmt.__class__}')




# if __name__ == '__main__':
#   import sys, argparse
#   parser = argparse.ArgumentParser()
#   parser.add_argument('--bmm', dest='bmm', action='store_true', default=False)
#   parser.add_argument('--tmm', dest='tmm', action='store_true', default=False)
#   parser.add_argument('fname', metavar='FILE', type=str, nargs=1)
#   opts = parser.parse_args(sys.argv[1:])
#   mm = 'tmm' if opts.tmm or not opts.bmm else 'bmm'
#   tac = compile_ast(opts.fname[0], mm)
