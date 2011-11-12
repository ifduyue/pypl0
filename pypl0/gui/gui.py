#!/usr/bin/env python
#-*- coding: utf-8 -*-

IN_GUI = True
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import pygtk
pygtk.require('2.0')
import gtk
import pango
import StringIO

class Gui(gtk.Window):
    filename = None
    p = None
    fio = None
    
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_size_request(600, 400)
        self.set_title("PyPL0 Compiler&Interpreter")
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("destroy", gtk.main_quit)
        
        vbox = gtk.VBox(False, 0)
        vbox.pack_start(self._create_menu_bar(), False, False, 0)
        
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_RIGHT)
        vbox.pack_start(self.notebook, True, True, 0)
        
        scrolled_window, self.source_code_buffer = self.__create_text_with_line_number()
        self._new_notebook_page(scrolled_window, 'Source Code')
        
        scrolled_window, self.pcode_buffer = self.__create_text()
        self._new_notebook_page(scrolled_window, 'P-code')
        
        scrolled_window, self.symbol_table_store = self.__create_symbol_table()
        self._new_notebook_page(scrolled_window, 'Symbol Table')
        
        scrolled_window, self.output_buffer = self.__create_text()
        self._new_notebook_page(scrolled_window, 'Output')
        
        scrolled_window, self.parsetree_treeview, self.parsetree_store = self._create_treeview_tree('Parse Tree')
        self._new_notebook_page(scrolled_window, 'Parse Tree')
        
        scrolled_window, self.ast_treeview, self.ast_store = self._create_treeview_tree('Abstract Syntax Tree')
        self._new_notebook_page(scrolled_window, 'AST')
        
        self.add(vbox)
        self.show_all()
    
    def _new_notebook_page(self, widget, label):
        l = gtk.Label('')
        l.set_text_with_mnemonic(label)
        self.notebook.append_page(widget,l)
        
    def _create_treeview_tree(self, title=''):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        
        store = gtk.TreeStore(str)
        tree_view = gtk.TreeView(store)
        tree_view.set_enable_tree_lines(True)
        
        parsetree = gtk.TreeViewColumn(title)
        tree_view.append_column(parsetree)
        
        cell = gtk.CellRendererText()
        parsetree.pack_start(cell, True)
        parsetree.add_attribute(cell, 'text', 0)
        
        scrolled_window.add(tree_view)
        
        return scrolled_window, tree_view, store
    
    def __create_symbol_table(self):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        
        store = gtk.ListStore(str, str, str, str, str)
        tree_view = gtk.TreeView(store)
        tree_view.set_rules_hint(True)
        scrolled_window.add(tree_view)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Name", rendererText, text=0)
        column.set_sort_column_id(0)    
        tree_view.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Kind", rendererText, text=1)
        column.set_sort_column_id(1)    
        tree_view.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Value", rendererText, text=2)
        column.set_sort_column_id(2)    
        tree_view.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Level", rendererText, text=3)
        column.set_sort_column_id(3)    
        tree_view.append_column(column)
        
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Addr", rendererText, text=4)
        column.set_sort_column_id(4)    
        tree_view.append_column(column)
        
        return scrolled_window, store
        
    
    def __fill_symbol_table(self, alist):
        for i in alist:
            self.symbol_table_store.append(i)
    
    def __fill_parsetree(self, store, alist):
        if len(alist) == 0:
            return
        
        a = alist[0]
        if not isinstance(a, list):
            child_store = self.parsetree_store.append(store, [str(a)])
            alist = alist[1:]
            for i in alist:
                if isinstance(i, list):
                    self.__fill_parsetree(child_store, i)
                else:
                    self.parsetree_store.append(child_store, [str(i)])
    
    def __fill_ast(self, store, alist):
        if len(alist) == 0:
            return
        
        a = alist[0]
        
        if not isinstance(a, list):
            child_store = self.ast_store.append(store, [str(a)])
            alist = alist[1:]
            for i in alist:
                if isinstance(i, list):
                    self.__fill_ast(child_store, i)
                elif str(i) != '[]':
                    self.ast_store.append(child_store, [str(i)])
    
    def __create_text(self):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        
        text_view = gtk.TextView()
        fontdesc = pango.FontDescription('Monospace 11')
        text_view.modify_font(fontdesc)
        scrolled_window.add(text_view)

        buffer = gtk.TextBuffer(None)
        text_view.set_buffer(buffer)
        text_view.set_editable(False)
        text_view.set_cursor_visible(False)
        
        return scrolled_window, buffer
    
    def __create_text_with_line_number(self):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_window.set_shadow_type(gtk.SHADOW_IN)
        
        from gtkcodebuffer import CodeBuffer, SyntaxLoader
        lang = SyntaxLoader("pl0")
        buffer = CodeBuffer(lang=lang)
        
        text_view = gtk.TextView(buffer)
        fontdesc = pango.FontDescription('Monospace 11')
        text_view.modify_font(fontdesc)
        scrolled_window.add(text_view)

        #text_view.set_editable(False)
        #text_view.set_cursor_visible(False)
        text_view.set_border_window_size(gtk.TEXT_WINDOW_LEFT, 20)
        text_view.connect("expose_event", self.line_numbers_expose)
        
        return scrolled_window, buffer
    
    def line_numbers_expose(self, widget, event, user_data=None):
        text_view = widget
  
        # See if this expose is on the line numbers window
        left_win = text_view.get_window(gtk.TEXT_WINDOW_LEFT)

        if event.window == left_win:
            type = gtk.TEXT_WINDOW_LEFT
            target = left_win
        else:
            return False
  
        first_y = event.area.y
        last_y = first_y + event.area.height

        x, first_y = text_view.window_to_buffer_coords(type, 0, first_y)
        x, last_y = text_view.window_to_buffer_coords(type, 0, last_y)

        numbers = []
        pixels = []
        count = self.get_lines(text_view, first_y, last_y, pixels, numbers)
  
        # Draw fully internationalized numbers!
        layout = widget.create_pango_layout("")
  
        for i in range(count):
            x, pos = text_view.buffer_to_window_coords(type, 0, pixels[i])
            str = "%d" % numbers[i]
            layout.set_text(str)
            widget.style.paint_layout(target, widget.state, False,
                                      None, widget, None, 2, pos + 2, layout)

        # don't stop emission, need to draw children
        return False
    
    def get_lines(self, widget, first_y, last_y, buffer_coords, numbers):
        text_view = widget
        # Get iter at first y
        iter, top = text_view.get_line_at_y(first_y)

        # For each iter, get its location and add it to the arrays.
        # Stop when we pass last_y
        count = 0
        size = 0

        while not iter.is_end():
            y, height = text_view.get_line_yrange(iter)
            buffer_coords.append(y)
            line_num = iter.get_line()
            numbers.append(line_num)
            count += 1
            if (y + height) >= last_y:
                break
            iter.forward_line()

        return count
        
    def _create_menu_bar(self):
        open_item = gtk.MenuItem("Open")
        open_item.connect("activate", self.openfile)
        quit_item = gtk.MenuItem("Quit")
        quit_item.connect("activate", gtk.main_quit)
        file_menu = gtk.Menu()
        file_menu.append(open_item)
        file_menu.append(quit_item)
        file_item = gtk.MenuItem("_File")
        file_item.set_submenu(file_menu)
        
        compile_item = gtk.MenuItem("Compile")
        compile_item.connect("activate", self.compile_cb)
        run_item = gtk.MenuItem("Run")
        run_item.connect("activate", self.run_cb)
        action_menu = gtk.Menu()
        action_menu.append(compile_item)
        action_menu.append(run_item)
        action_item = gtk.MenuItem("_Action")
        action_item.set_submenu(action_menu)
        
        about_item = gtk.MenuItem("About")
        about_item.connect("activate", self.about)
        help_menu = gtk.Menu()
        help_menu.append(about_item)
        help_item = gtk.MenuItem("_Help")
        help_item.set_submenu(help_menu)
        
        menu_bar = gtk.MenuBar()
        menu_bar.append(file_item)
        menu_bar.append(action_item)
        menu_bar.append(help_item)
        
        return menu_bar
    
    def about(self, *w):
        about = gtk.AboutDialog()
        about.set_program_name("PyPL0")
        about.set_version("1.0")
        about.set_copyright("(c) lyxint")
        about.set_comments("PyPL0 is a python implemented PL/0 language compiler and interpreter")
        about.set_website("http://github.com/elyesdu/pypl0")
        about.run()
        about.destroy()
    
    def openfile(self, *w):
        openfile = gtk.FileChooserDialog("Open PL/0 source file..", self, gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        response = openfile.run()
        if response == gtk.RESPONSE_OK:
            self.filename = openfile.get_filename()
            self.p = None
            f = open(self.filename)
            content = f.read()
            f.close()
            self.source_code_buffer.set_text(content)
            self.output_buffer.set_text('')
            self.pcode_buffer.set_text('')
            self.symbol_table_store.clear()
            self.notebook.set_current_page(0)
        openfile.destroy()
    
    def compile_cb(self, *w):
        if not self.filename:
            return
        from backend.parser import Parser
        fio = StringIO.StringIO()
        start_iter = self.source_code_buffer.get_start_iter()
        end_iter = self.source_code_buffer.get_end_iter()
        fio.write(self.source_code_buffer.get_text(start_iter, end_iter))
        fio.seek(0)
        self.p = Parser(fio, True)
        self.pcode_buffer.set_text('')
        self.symbol_table_store.clear()
        if self.p.error:
            self.output_buffer.set_text(self.p.error)
            self.notebook.set_current_page(3)
        else:
            self.pcode_buffer.set_text(self.p.get_formated_pcode())
            self.__fill_symbol_table(self.p.get_formated_table())
            self.__fill_parsetree(None, self.p.result)
            self.parsetree_treeview.expand_all()
            self.__fill_ast(None, self.p.get_formated_ast())
            self.ast_treeview.expand_all()
            
            self.notebook.set_current_page(1)
        
    
    def run_cb(self, *w):
        if not self.filename or not self.p:
            return
        if self.p.error:
            self.output_buffer.set_text(self.p.error)
            self.notebook.set_current_page(3)
        else:
            from backend.interpreter import Interpreter
            Interpreter.IN_GUI = True
            i = Interpreter(self.p.pcode.pcode)
            i.output_buffer = self.output_buffer
            self.notebook.set_current_page(3)
            i.run(self)
            #self.output_buffer.set_text(i.result)
            
        
def main():
    gtk.main()
    
if __name__ == '__main__':
    Gui()
    main()
