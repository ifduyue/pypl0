#!/usr/bin/env python
#-*- coding: utf-8 -*-

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

class Token:  
    def __init__(self, content, token_type, line_number):
        self.content = content
        self.token_type = token_type
        self.line_number = line_number
    
    def __repr__(self):
        return self.token_type+'('+self.content+')'
    
     
literals = {
    '+' : 'PLUS',
    '-' : 'MINUS',
    '*' : 'MUL',
    '/' : 'DIV',
    '=' : 'EQ',
    '<' : 'LT',
    '>' : 'GT',
    '<=' : 'LE',
    '>=' : 'GE',
    '<>' : 'NE',
    '(' : 'LPAREN',
    ')' : 'RPAREN',
    ',' : 'COMMA',
    ';' : 'SEMICOLON',
    '.' : 'DOT',
    ':=' : 'ASSIGN',
    'begin' : 'BEGIN',
    'call' : 'CALL',
    'const' : 'CONST',
    'do' : 'DO',
    'end' : 'END',
    'if' : 'IF',
    'in' : 'IN',
    'odd' : 'ODD',
    'out' : 'OUT',
    'procedure' : 'PROCEDURE',
    'then' : 'THEN',
    'var' : 'VAR',
    'while' : 'WHILE',
    'read' : 'READ',
    'write' : 'WRITE',
}

for i in literals.values():
    setattr(Token, i, i)
setattr(Token, 'IDENT', 'IDENT')
setattr(Token, 'NUMBER', 'NUMBER')
setattr(Token, 'EOF', 'EOF')
setattr(Token, 'ILLEGAL', 'ILLEGAL')

class Scanner:
    def __init__(self, src_file, opened=False):
        if opened:
            self._file = src_file
        else:
            self._file = open(src_file)
        self._cur_line = 0
        self._buffer = []
        self.opened = opened
        
    def __del__(self):
        if not self.opened:
            self._file.close()
        
    def _tokenize_line(self, line):
        line = line.rstrip();
        while line:
            line = line.lstrip()
            if line[:2] in ('<=', '>=', ':=', '<>'):
                t = Token(line[:2], getattr(Token, literals[line[:2]]), self._cur_line)
                self._buffer.append(t)
                line = line[2:]
                continue
            elif line[0] in ('+', '-', '*', '/', '>', '<', '(', ')', ';', ',', '.', '='):
                t = Token(line[0], getattr(Token, literals[line[0]]), self._cur_line)
                self._buffer.append(t)
                line = line[1:]
                continue
            else:
                import re
                
                m = re.match('[a-zA-Z]\w*', line)
                if m:
                    content = m.group()
                    if literals.has_key(content):
                        t = Token(content, getattr(Token, literals[content]), self._cur_line)
                    else:
                        t = Token(content, Token.IDENT, self._cur_line)
                    self._buffer.append(t)
                    line = line[len(content):]
                    continue
                
                m = re.match('\d+', line)
                if m:
                    content = m.group()
                    self._buffer.append(Token(content, Token.NUMBER, self._cur_line))
                    line = line[len(content):]
                    continue
                
                m = re.match('\S+', line)
                content = m.group()
                self._buffer.append(Token(content, Token.ILLEGAL, self._cur_line))
                line = line[len(content):]
        
    def _fill_buffer(self, size=1):
        while len(self._buffer) < size:
            line = self._file.readline()
            if not line:
                self._buffer.append(Token('', Token.EOF, self._cur_line))
                continue
            self._cur_line += 1
            self._tokenize_line(line)
    
    def look_ahead(self, size=1):
        self._fill_buffer(size)
        return self._buffer[:size]
        
    def next_token(self):
        self._fill_buffer(1)
        return self._buffer.pop(0) 