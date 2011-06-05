#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from scanner import Token

class Node:
    def __getitem__(self, i):
        return self.children[i]
    
    def __iter__(self):
        return self.children
    
    def __repr__(self):
        return self.__class__.__name__
    
class Program(Node):
    def __init__(self, block):
        self.block = block
        self.children = [self.__class__.__name__, block]
        
class Block(Node):
    def __init__(self, const_name, const_num, var_name, procedure, statement):
        self.const_name, self.const_num, self.var_name, self.procedure, self.statement = const_name, const_num, var_name, procedure, statement
        self.children = [self.__class__.__name__, const_name, const_num, var_name]
        self.children.extend(procedure)
        self.children.append(statement)

class Procedure(Node):
    def __init__(self, name, block):
        self.name, self.block = name, block
        self.children = [self.__class__.__name__, name, block]

class Statement(Node):
    pass

class AssignStatement(Statement):
    def __init__(self, name, expression):
        self.name, self.expression = name, expression
        self.children = [self.__class__.__name__, name, expression]

class CallStatement(Statement):
    def __init__(self, procedure_name):
        self.procedure_name = procedure_name
        self.children = [self.__class__.__name__, procedure_name]
        
class BeginEndStatement(Statement):
    def __init__(self, statement):
        self.statement = statement
        self.children = [self.__class__.__name__]
        self.children.extend(statement)
        
class IfStatement(Statement):
    def __init__(self, condition, statement):
        self.condition, self.statement = condition, statement
        self.children = [self.__class__.__name__, condition, statement]
        
class WhileStatement(Statement):
    def __init__(self, condition, statement):
        self.condition, self.statement = condition, statement
        self.children = [self.__class__.__name__, condition, statement]

class WriteStatement(Statement):
    def __init__(self, expression):
        self.expression = expression
        self.children = [self.__class__.__name__]
        self.children.extend(expression)

class ReadStatement(Statement):
    def __init__(self, var):
        self.var = var
        self.children = [self.__class__.__name__]
        self.children.extend(var)

class Condition(Node):
    pass

class OddCondition(Condition):
    def __init__(self, expression):
        self.expression = expression
        self.children = [self.__class__.__name__, expression]
        
class BinaryCondition(Condition):
    def __init__(self, lexpression, rexpression, compare):
        self.lexpression, self.rexpression, self.compare = lexpression, rexpression, compare
        self.children = [self.__class__.__name__, lexpression, rexpression, compare]
        
class Expression(Node):
    def __init__(self, sign, term):
        self.sign, self.term = sign, term
        self.children = [self.__class__.__name__, sign]
        self.children.extend(term)
        
class Term(Node):
    def __init__(self, sign, factor):
        self.sign, self.factor = sign, factor
        self.children = [self.__class__.__name__, sign]
        self.children.extend(factor)
        
class Factor(Node):
    pass

class IdentFactor(Factor):
    def __init__(self, name):
        self.name = name
        self.children = [self.__class__.__name__, name]
        
class NumberFactor(Factor):
    def __init__(self, number):
        self.number = number
        self.children = [self.__class__.__name__, number]
        
class ExpressionFactor(Factor):
    def __init__(self, expression):
        self.expression = expression
        self.children = [self.__class__.__name__, expression]

class AST:
    def __init__(self, parsetree):
        self.parsetree = parsetree
        self.result = self.generate(parsetree)
        
    def get_formated_ast(self, alist):
        result = [str(alist[0])]
        for e in alist[1:]:
            if self._isInternalNode(e):
                result.append(self.get_formated_ast(e))
            else:
                result.append(str(e))
        
        return result
            
    def _isInternalNode(self, node):
        return node and hasattr(node, '__iter__') and isinstance(node[0], str)
        
    def generate(self, alist):
        if hasattr(alist, '__iter__'):
            if alist[0] == '<program>' and alist[1][0] == '<block>':
                return Program(self.generate(alist[1]))
            elif alist[0] == '<block>':
                const_name, const_num, var_name, procedure, statement = [], [], [], [], None
                
                lst = alist[1:]
                
                if lst and hasattr(lst[0], 'token_type') and lst[0].token_type == Token.CONST:
                    lst = lst[1:]
                    for i, token in enumerate(lst):
                        if token.token_type == Token.SEMICOLON:
                            lst = lst[i+1:]
                            break
                        elif token.token_type == Token.IDENT:
                            const_name.append(token)
                        elif token.token_type == Token.NUMBER:
                            const_num.append(token)
                
                if lst and getattr(lst[0], 'token_type', False) == Token.VAR:
                    lst = lst[1:]
                    for i, token in enumerate(lst):
                        if token.token_type == Token.SEMICOLON:
                            lst = lst[i+1:]
                            break
                        elif token.token_type == Token.IDENT:
                            var_name.append(token)
                
                while lst and getattr(lst[0], 'token_type', False) == Token.PROCEDURE:
                    procedure.append(Procedure(lst[1], self.generate(lst[3])))
                    lst = lst[5:]
                
                if lst and hasattr(lst[0], '__iter__') and lst[0][0] == '<statement>' and lst[0][1:]:
                    statement = self.generate(lst[0])
                
                return Block(const_name, const_num, var_name, procedure, statement)
            elif alist[0] == '<statement>':
                lst = alist[1:]
                
                if lst and getattr(lst[0], 'token_type', False) == Token.IDENT:
                    return AssignStatement(lst[0], self.generate(lst[2]))
                elif lst and getattr(lst[0], 'token_type', False) == Token.CALL:
                    return CallStatement(lst[1])
                elif lst and getattr(lst[0], 'token_type', False) == Token.BEGIN:
                    statement = []
                    for i in lst[1:]:
                        if getattr(i, 'token_type', False) == Token.END:
                            break
                        elif hasattr(i, '__iter__') and i[0] == '<statement>' and i[1:]:
                            statement.append(self.generate(i))
                    return BeginEndStatement(statement)
                elif lst and getattr(lst[0], 'token_type', False) == Token.IF:
                    return IfStatement(self.generate(lst[1]), self.generate(lst[3]))
                elif lst and getattr(lst[0], 'token_type', False) == Token.WHILE:
                    return WhileStatement(self.generate(lst[1]), self.generate(lst[3]))
                elif lst and getattr(lst[0], 'token_type', False) == Token.WRITE:
                    expression = []
                    
                    for i in lst[1:]:
                        if getattr(i, 'token_type', False) == Token.RPAREN:
                            break
                        elif hasattr(i, '__iter__') and i[0] == '<expression>' and i[1:]:
                            expression.append(self.generate(i))
                    return WriteStatement(expression)
                elif lst and getattr(lst[0], 'token_type', False) == Token.READ:
                    var = []
                    expression = []
                    for i in lst[1:]:
                        if getattr(i, 'token_type', False) == Token.RPAREN:
                            break
                        elif getattr(i, 'token_type', False) == Token.IDENT:
                            var.append(i)
                    return ReadStatement(var)
            elif alist[0] == '<condition>':
                lst = alist[1:]
            
                if lst and getattr(lst[0], 'token_type', False) == Token.ODD:
                    return OddCondition(self.generate(lst[1]))
                elif lst and hasattr(lst[0], '__iter__') and lst[0][0] == '<expression>':
                    return BinaryCondition(self.generate(lst[0]), self.generate(lst[2]), self.generate(lst[1]))
            elif alist[0] == '<expression>':
                sign, term = [], []
                lst = alist[1:]
                
                for i in lst:
                    if getattr(i, 'token_type', False) in (Token.PLUS, Token.MINUS):
                        sign.append(i)
                    elif hasattr(i, '__iter__') and i[0] == '<term>':
                        term.append(self.generate(i))
                return Expression(sign, term)
            elif alist[0] == '<term>':
                sign, factor = [], []
                lst = alist[1:]
                
                for i in lst:
                    if getattr(i, 'token_type', False) in (Token.MUL, Token.DIV):
                        sign.append(i)
                    elif hasattr(i, '__iter__') and i[0] == '<factor>':
                        factor.append(self.generate(i))
                return Term(sign, factor)
            elif alist[0] == '<factor>':
                lst = alist[1:]
                if lst and getattr(lst[0], 'token_type', False) == Token.IDENT:
                    return IdentFactor(lst[0])
                elif lst and getattr(lst[0], 'token_type', False) == Token.NUMBER:
                    return NumberFactor(lst[0])
                elif lst and getattr(lst[0], 'token_type', False) == Token.LPAREN:
                    return ExpressionFactor(self.generate(lst[1]))
        else:
            pass
    

