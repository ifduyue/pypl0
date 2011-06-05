#!/usr/bin/env python
#-*- coding: utf-8 -*-
from scanner import Scanner, Token
from ast import AST

class TableItem:
    def __init__(self, name, kind, val='', level='', addr='', size=''):
        self.name, self.kind, self.val, self.level, self.addr, self.size = name, kind, val, level, addr, size
    
    def __repr__(self):
        import StringIO
        f = StringIO.StringIO()
        print >> f, self.name, self.kind, self.val, self.level, self.addr, self.size
        return f.getvalue()

for i in ('const', 'var', 'procedure'):
    setattr(TableItem, i.upper(), i)

class Table:
    def __init__(self):
        self.table = []
        #self.dx = 3  # 0,1,2 for SL,DL,RA
    
    def add(self, tableitem):
        self.table.append(tableitem)
        
    def len(self):
        return len(self.table)
    
    def position(self, ident, lev):
        for i, j in enumerate(reversed(self.table)):
            if j.name == ident:
                return self.len() - 1 - i
        return -1

class PcodeItem:
    def __init__(self, f, l, a):
        self.f, self.l, self.a = f, l, a
    
    def __repr__(self):
        return self.f + '-' + str(self.l) + '-' + str(self.a)

for i in ('lit', 'lod', 'sto', 'cal', 'int', 'jmp', 'jpc', 'opr'):
    setattr(PcodeItem, i.upper(), i)

#lit 0, a : load constant a to stack top
#opr 0, a : excute operation a
#lod l, a : load variable a with level l to stack top
#sto l, a : store stack top value to variable a with level l
#cal l, a : call procedure a at level l
#int 0, a : increment t-register by a stack
#jmp 0, a : jump to a
#jpc 0, a : jump conditional to a


class Pcode:
    def __init__(self):
        self.pcode = []
    
    def add(self, pcodeitem):
        self.pcode.append(pcodeitem)
        
    def len(self):
        return len(self.pcode)

class Parser:
    def __init__(self, src_file, opened=False):
        self.opened = opened
        self.scanner = Scanner(src_file, opened)
        self.look_ahead_one = lambda : self.scanner.look_ahead()[0]
        self.result = None
        self.pcode = Pcode()
        self.table = Table()
        self.error = None
        self.tx = []
        self.program()
        
    def get_formated_ast(self):
        ast = AST(self.result)
        tree = ast.generate(self.result)
        return ast.get_formated_ast(tree)
        
    def get_formated_pcode(self):
        result = ''
        for key, val in enumerate(self.pcode.pcode):
            result += str(key).zfill(4) + '    ' + val.f + ' ' + str(val.l).rjust(4) + ' ' + str(val.a).rjust(4) + '\n'
        return result
    
    def get_formated_table(self):
        result = []
        for i in self.table.table:
            result.append([i.name, i.kind, str(i.val), str(i.level), str(i.addr)])
        return result
    
    def _expect(self, token_type):
        next_token = self.scanner.next_token()
        if next_token.token_type == token_type:
            return next_token
        else:
            if not self.error:
                self.pcode.error = True
                self.error = 'line %d: expect %s, not %s(%s)' % (next_token.line_number, token_type, next_token.token_type, next_token.content)
            else:
                 self.error += '\nline %d: expect %s, not %s(%s)' % (next_token.line_number, token_type, next_token.token_type, next_token.content)
    
    def program(self, lev=0): 
        self.result = ['<program>', self.block(lev), self._expect(Token.DOT), self._expect(Token.EOF)]
        
    def block(self, lev):
        result = ['<block>']
        
        dx = 3
        tx = self.table.len()
        cx = self.pcode.len()
        self.pcode.add(PcodeItem(PcodeItem.JMP, 0, 0))
        
        if self.look_ahead_one().token_type == Token.CONST:
            result.extend(
                map(self._expect, (Token.CONST, Token.IDENT, Token.EQ, Token.NUMBER))
            )
            self.table.add(TableItem(result[-3].content, 'const', int(result[-1].content)))
            
            while self.look_ahead_one().token_type == Token.COMMA:
                result.extend(
                    map(self._expect, (Token.COMMA, Token.IDENT, Token.EQ, Token.NUMBER))
                )
                self.table.add(TableItem(result[-3].content, 'const', int(result[-1].content)))
                
            result.append(self._expect(Token.SEMICOLON))
        
        if self.look_ahead_one().token_type == Token.VAR:
            result.extend(
                map(self._expect, (Token.VAR, Token.IDENT))
            )
            if result[-1]:
                self.table.add(TableItem(result[-1].content, 'var', '', lev, dx))
                dx += 1
            
            while self.look_ahead_one().token_type == Token.COMMA:
                result.extend(
                    map(self._expect, (Token.COMMA, Token.IDENT))
                )
                self.table.add(TableItem(result[-1].content, 'var', '', lev, dx))
                dx += 1
                
            result.append(self._expect(Token.SEMICOLON))
            
        while self.look_ahead_one().token_type == Token.PROCEDURE:
            result.extend(
                map(self._expect, (Token.PROCEDURE, Token.IDENT, Token.SEMICOLON))
            )
            self.tx.append(self.table.len())
            self.table.add(TableItem(result[-2].content, 'procedure', level=lev))
            #self.table.add(TableItem(result[-2].content, 'procedure', level=lev, addr=self.pcode.len() + 1))
            #self.table.add(TableItem(result[-2].content, 'procedure', level=lev, addr=dx))
            #dx += 1
            result.append(self.block(lev+1))
            result.append(self._expect(Token.SEMICOLON))
        
        if len(self.tx) != 0:
            self.table.table[self.tx.pop()].addr = self.pcode.len()
        self.pcode.pcode[cx].a = self.pcode.len() #return to main procedure
        #if self.table.len() > tx:
            #self.table.table[tx].addr = self.pcode.len()
        #self.table.table[tx].size = dx
        
        self.pcode.add(PcodeItem(PcodeItem.INT, 0, dx))
        result.append(self.statement(lev))
        self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 0))
        
        return result
    
    def statement(self, lev):
        result = ['<statement>']
        
        t = self.look_ahead_one()
        if t.token_type == Token.IDENT:
            result.extend(
                map(self._expect, (Token.IDENT, Token.ASSIGN))
            )
            
            i = self.table.position(t.content, lev);
            if i == -1 or self.table.table[i].kind != 'var':
                if not self.error:
                    self.pcode.error = True
                    self.error = 'line %d: %s is not variable' % (t.line_number, t.content)
                else:
                    self.error += '\nline %d: %s is not variable' % (t.line_number, t.content)
                return '<error>'
            
            result.append(self.expression(lev))
            self.pcode.add(PcodeItem(PcodeItem.STO, lev - self.table.table[i].level, self.table.table[i].addr))
        elif t.token_type == Token.CALL:
            result.extend(
                map(self._expect, (Token.CALL, Token.IDENT))
            )

            i = self.table.position(result[-1].content, lev)
            if i == -1 or self.table.table[i].kind != 'procedure':
                if not self.error:
                    self.pcode.error = True
                    self.error = 'line %d: %s is not procedure' % (result[-1].line_number, t.content)
                else:
                    self.error += '\nline %d: %s is not procedure' % (result[-1].line_number, t.content)
                return '<error>'
            
            self.pcode.add(PcodeItem(PcodeItem.CAL, lev - int(self.table.table[i].level), self.table.table[i].addr))
        elif t.token_type == Token.BEGIN:
            result.append(self._expect(Token.BEGIN))
            result.append(self.statement(lev))
            while self.look_ahead_one().token_type == Token.SEMICOLON:
                result.append(self._expect(Token.SEMICOLON))
                result.append(self.statement(lev))
            result.append(self._expect(Token.END))
        elif t.token_type == Token.IF:
            result.append(self._expect(Token.IF))
            result.append(self.condition(lev))
            result.append(self._expect(Token.THEN))
            cx = self.pcode.len()
            self.pcode.add(PcodeItem(PcodeItem.JPC, 0, 0))
            result.append(self.statement(lev))
            self.pcode.pcode[cx].a = self.pcode.len()
        elif t.token_type == Token.WHILE:
            result.append(self._expect(Token.WHILE))
            cx1 = self.pcode.len()
            result.append(self.condition(lev))
            cx2 = self.pcode.len()
            self.pcode.add(PcodeItem(PcodeItem.JPC, 0, 0))
            result.append(self._expect(Token.DO))
            result.append(self.statement(lev))
            self.pcode.add(PcodeItem(PcodeItem.JMP, 0, cx1))
            self.pcode.pcode[cx2].a = self.pcode.len()
        elif t.token_type == Token.READ:
            result.append(self._expect(Token.READ))
            result.append(self._expect(Token.LPAREN))
            result.append(self._expect(Token.IDENT))
            i = self.table.position(result[-1].content, lev)
            if i == -1 or self.table.table[i].kind != 'var':
                if not self.error:
                    self.pcode.error = True
                    self.error = 'line %d: %s is not variable' % (result[-1].line_number, result[-1].content)
                else:
                    self.error += '\nline %d: %s is not variable' % (result[-1].line_number, result[-1].content)
                return '<error>'
            self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 16))
            self.pcode.add(PcodeItem(PcodeItem.STO, lev - self.table.table[i].level, self.table.table[i].addr))
            while self.look_ahead_one().token_type == Token.COMMA:
                result.append(self._expect(Token.COMMA))
                result.append(self._expect(Token.IDENT))
                i = self.table.position(result[-1].content, lev)
                if i == -1 or self.table.table[i].kind != 'var':
                    if not self.error:
                        self.pcode.error = True
                        self.error = 'line %d: %s is not variable' % (result[-1].line_number, result[-1].content)
                    else:
                        self.error += '\nline %d: %s is not variable' % (result[-1].line_number, result[-1].content)
                    return '<error>'
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 16))
                self.pcode.add(PcodeItem(PcodeItem.STO, lev - self.table.table[i].level, self.table.table[i].addr))
            result.append(self._expect(Token.RPAREN))
        elif t.token_type == Token.WRITE:
            result.append(self._expect(Token.WRITE))
            result.append(self._expect(Token.LPAREN))
            result.append(self.expression(lev))
            self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 14))
            while self.look_ahead_one().token_type == Token.COMMA:
                result.append(self._expect(Token.COMMA))
                result.append(self.expression(lev))
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 14))
            result.append(self._expect(Token.RPAREN))
            self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 15))
        
        return result
    
    def condition(self, lev):
        result = ['<condition>']
        
        if self.look_ahead_one().token_type == Token.ODD:
            result.append(self._expect(Token.ODD))
            result.append(self.expression(lev))
            self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 6))
        else:
            result.append(self.expression(lev))
            t = self.look_ahead_one()
            if t.token_type == Token.EQ:
                result.append(self._expect(Token.EQ))
            elif t.token_type == Token.NE:
                result.append(self._expect(Token.NE))
            elif t.token_type == Token.LT:
                result.append(self._expect(Token.LT))
            elif t.token_type == Token.LE:
                result.append(self._expect(Token.LE))
            elif t.token_type == Token.GT:
                result.append(self._expect(Token.GT))
            elif t.token_type == Token.GE:
                result.append(self._expect(Token.GE))
            else:
                if not self.error:
                    self.pcode.error = True
                    self.error = 'line %d: %s should be one of (<, <=, =, >, >=, <>)' % (t.line_number, t.content)
                else:
                    self.error += '\nline %d: %s should be one of (<, <=, =, >, >=, <>)' % (t.line_number, t.content)
                return '<error>'
            
            result.append(self.expression(lev))
            
            if t.token_type == Token.EQ:
               self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 8))
            elif t.token_type == Token.NE:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 9))
            elif t.token_type == Token.LT:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 10))
            elif t.token_type == Token.LE:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 13))
            elif t.token_type == Token.GT:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 12))
            elif t.token_type == Token.GE:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 11))
                
        return result
    
    def expression(self, lev):
        result = ['<expression>']
        
        t = self.look_ahead_one()
        
        if t.token_type == Token.PLUS:
            result.append(self._expect(Token.PLUS))
        elif t.token_type == Token.MINUS:
            result.append(self._expect(Token.MINUS))
        result.append(self.term(lev))
        
        if t.token_type == Token.MINUS:
            self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 1))
        
        t = self.look_ahead_one()
        while t.token_type in (Token.PLUS, Token.MINUS):
            result.append(self._expect(t.token_type))
            result.append(self.term(lev))
            if t.token_type == Token.PLUS:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 2))
            elif t.token_type == Token.MINUS:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 3))
            t = self.look_ahead_one()
            
        return result
    
    def term(self, lev):
        result = ['<term>']
        
        result.append(self.factor(lev))
        
        t = self.look_ahead_one()
        while t.token_type in (Token.MUL, Token.DIV):
            result.append(self._expect(t.token_type))
            result.append(self.factor(lev))
            
            if t.token_type == Token.MUL:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 4))
            elif t.token_type == Token.DIV:
                self.pcode.add(PcodeItem(PcodeItem.OPR, 0, 5))
                
            t = self.look_ahead_one()
            
        return result
    
    def factor(self, lev):
        result = ['<factor>']
        
        t = self.look_ahead_one()
        if t.token_type == Token.IDENT:
            result.append(self._expect(Token.IDENT))
            i = self.table.position(t.content, lev)
            if i == -1:
                if not self.error:
                    self.pcode.error = True
                    self.error = 'line %d: %s not declared' % (t.line_number, t.content)
                else:
                    self.error += '\nline %d: %s not declared' % (t.line_number, t.content)
                return '<error>'
            ident = self.table.table[i]
            if ident.kind == 'const':
                self.pcode.add(PcodeItem(PcodeItem.LIT, 0, ident.val))
            elif ident.kind == 'var':
                self.pcode.add(PcodeItem(PcodeItem.LOD, lev - ident.level, ident.addr))
            elif ident.kind == 'procedure':
                if not self.error:
                    self.pcode.error = True
                    self.error = 'line %d: factor should not have procedure %s' % (t.line_number, t.content)
                else:
                    self.error += '\nline %d: factor should not have procedure %s' % (t.line_number, t.content)
                return '<error>'
        elif t.token_type == Token.NUMBER:
            result.append(self._expect(Token.NUMBER))
            self.pcode.add(PcodeItem(PcodeItem.LIT, 0, result[-1].content))
        elif t.token_type == Token.LPAREN:
            result.append(self._expect(Token.LPAREN))
            result.append(self.expression(lev))
            result.append(self._expect(Token.RPAREN))
        else:
            if not self.error:
                self.pcode.error = True
                self.error = 'line %d: wrong token %s here' % (t.line_number, t.content)
            else:
                self.error += '\nline %d: wrong token %s here' % (t.line_number, t.content)
            return '<error>'
    
        return result