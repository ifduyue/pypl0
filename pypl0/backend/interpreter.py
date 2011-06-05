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

class Interpreter:
    IN_GUI = False
    
    def __init__(self, pcode):
        # p: pointer to current instruction of current block
        # b: pointer to stack base of current block
        # t: pointer to stack top of current block
        self.p, self.b = 0, 0
        # as I use python's list as stack, the length of the stack is t.
        self.stack = [] # for SL, DL and RA
        self.pcode = pcode
        self.result = ''
        self.output_buffer = None
    
    def run(self, *w):
        self.w = w
        while True:
            self.p = int(self.p)
            i = self.pcode[self.p]
            self.p += 1
            getattr(self, i.f)(i)
            
            if self.p == 0:
                break
        #print self.result
            
    def lit(self, pcodeitem):
        self.stack.append(int(pcodeitem.a))
        
    def opr(self, pcodeitem):
        getattr(self, 'opr_' + str(pcodeitem.a))(pcodeitem)
        
    def opr_0(self, pcodeitem):
        tmp = self.b
        self.p = self.stack[self.b + 2]
        self.b = self.stack[self.b + 1]
        del self.stack[tmp:]
    
    def opr_1(self, pcodeitem):
        self.stack[-1] = -self.stack[-1]
    
    def opr_2(self, pcodeitem):
        self.stack.append(self.stack.pop()+self.stack.pop())
    
    def opr_3(self, pcodeitem):
        self.stack.append(-self.stack.pop()+self.stack.pop())
    
    def opr_4(self, pcodeitem):
        self.stack.append(self.stack.pop()*self.stack.pop())
    
    def opr_5(self, pcodeitem):
        tmp1, tmp2 = self.stack.pop(), self.stack.pop()
        self.stack.append(tmp2/tmp1)
    
    def opr_6(self, pcodeitem):
        self.stack.append(self.stack.pop()%2)
    
    def opr_7(self, pcodeitem):
        pass # not defined
    
    def opr_8(self, pcodeitem):
        if self.stack.pop() == self.stack.pop():
            self.stack.append(1)
        else:
            self.stack.append(0)
    
    def opr_9(self, pcodeitem):
        if self.stack.pop() <> self.stack.pop():
            self.stack.append(1)
        else:
            self.stack.append(0)
    
    def opr_10(self, pcodeitem):
        if self.stack.pop() > self.stack.pop():
            self.stack.append(1)
        else:
            self.stack.append(0)
    
    def opr_11(self, pcodeitem):
        if self.stack.pop() <= self.stack.pop():
            self.stack.append(1)
        else:
            self.stack.append(0)
    
    def opr_12(self, pcodeitem):
        if self.stack.pop() < self.stack.pop():
            self.stack.append(1)
        else:
            self.stack.append(0)
    
    def opr_13(self, pcodeitem):
        if self.stack.pop() >= self.stack.pop():
            self.stack.append(1)
        else:
            self.stack.append(0)
    
    def opr_14(self, pcodeitem):
        self.result += str(self.stack.pop()) + ' '
        
    def opr_15(self, pcodeitem):
        self.result += '\n'
        if self.IN_GUI:
            self.output_buffer.insert(self.output_buffer.get_end_iter(), self.result)
            self.result = ''
        else:
            print self.result
        
    def opr_16(self, pcodeitem):
        if self.IN_GUI:
            import gtk
            def dialog():
                dlg = gtk.Dialog("Input request", self.w[0], gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
                label = gtk.Label("Please enter an integer:")
                dlg.vbox.pack_start(label, True, True)
                label.show()
                entry = gtk.Entry(14)
                dlg.vbox.pack_start(entry, True, True)
                entry.show()
                dlg.run()
                return dlg, entry.get_text()
            dlg, i = dialog()
            i = i.strip()
            while len(i) == 0 or not i.isdigit():
                dlg.destroy()
                dlg, i = dialog()
                i = i.strip()
            dlg.destroy()
            i = int(i)
        else:
            i = raw_input('Please enter an integer: ');
            i = i.strip()
            while len(i) == 0 or not i.isdigit():
                i = raw_input('Invalid input. Please enter an integer: ')
                i = i.strip()
            i = int(i)
        self.stack.append(i)
    
    def lod(self, pcodeitem):
        self.stack.append(self.stack[self.base(pcodeitem.l, self.b) + pcodeitem.a])
        
    def sto(self, pcodeitem):
        self.stack[self.base(pcodeitem.l, self.b) + pcodeitem.a] = self.stack.pop()
    
    def cal(self, pcodeitem):
        self.tmp = [self.base(pcodeitem.l, self.b), self.b, self.p]
        self.b = len(self.stack)
        self.p = pcodeitem.a
        
    def int(self, pcodeitem):
        if getattr(self,'tmp' , False):
            self.stack.extend(self.tmp)
            del self.tmp
            if pcodeitem.a > 3:
                self.stack.extend([0] * (pcodeitem.a - 3))
        else:
            self.stack.extend([0] * pcodeitem.a)
        
    def jmp(self, pcodeitem):
        self.p = pcodeitem.a
    
    def jpc(self, pcodeitem):
        
        if self.stack[-1] == 0:
            self.p = pcodeitem.a
        self.stack.pop()
        
    
    def base(self, l, b):
        while l > 0:
            b = self.stack[b]
            l -= 1
        return b