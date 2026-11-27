#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NewTrobat Editor — редактор code.xml проектов NewCatroid (.newtrobat) на Python/tkinter.

Запуск:   python newtrobat_editor.py [проект.newtrobat | code.xml]
Нужны:    Python 3.9+ с tkinter (стандартная поставка), файлы newtrobat_core.py и newtrobat_catalog.py рядом.
"""
import base64
import os
import sys
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, simpledialog, ttk

import newtrobat_catalog as C
from newtrobat_core import (
    BRICK_PKG, FNode, FormulaSyntaxError, Project, brick_title, child, child_text, element_xml, element_summary,
    elem_to_node, formula_container, formula_key, formula_text, get_formulas, is_brick, is_object, is_script,
    make_brick, make_list, make_look, make_object, make_scene, make_script, make_sound, make_variable, new_uuid,
    node_to_text, parent_map, parse_formula_text, parse_xml, rename_in_formulas, resolve_ref, retarget_groups,
    script_title, search, set_formula, unique_name, unused_files, validate, OBJECT_TYPES, NODE_TYPES,
)

APP_TITLE = 'NewTrobat Editor'
LIST_LABELS = {
    'loopBricks': 'Тело', 'ifBranchBricks': 'Тогда', 'elseBranchBricks': 'Иначе', 'nestedBricks': 'Вложенные блоки',
    'threadBricks': 'Поток', 'tryBricks': 'try', 'catchBricks': 'catch', 'finallyBricks': 'finally',
    'lookList': 'Образы', 'soundList': 'Звуки', 'userVariables': 'Локальные переменные',
    'userLists': 'Локальные списки', 'userDefinedBrickList': 'Пользовательские блоки', 'nfcTagList': 'NFC-метки',
    'programVariableList': 'Глобальные переменные', 'programListOfLists': 'Глобальные списки',
    'programMultiplayerVariableList': 'Переменные мультиплеера', 'settings': 'Настройки', 'header': 'Заголовок',
}
OBJECT_LABELS = {'Sprite': 'Объект', 'GroupSprite': 'Группа', 'GroupItemSprite': 'Элемент группы'}
HIDDEN_LEAVES = {'brickId', 'scriptId', 'commentedOut'}
REF_TAGS = ('look', 'sound', 'userVariable', 'userList')
OBJ_REF_TAGS = ('pointedObject', 'destinationSprite', 'objectToClone')


# ---------------------------------------------------------------------------
# Вспомогательные виджеты
# ---------------------------------------------------------------------------

class ScrollFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        for w in (self.canvas, self.inner):
            w.bind('<MouseWheel>', self._wheel)
            w.bind('<Button-4>', lambda e: self.canvas.yview_scroll(-3, 'units'))
            w.bind('<Button-5>', lambda e: self.canvas.yview_scroll(3, 'units'))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 40) or (-1 if e.delta > 0 else 1), 'units')

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.canvas.yview_moveto(0)


class Picker(tk.Toplevel):
    """Выбор из списка с поиском. items: [(key, текст, описание, категория)]."""

    def __init__(self, master, title, items, categories=None, allow_new=None):
        super().__init__(master)
        self.title(title)
        self.geometry('760x520')
        self.transient(master)
        self.items, self.result, self.shown = items, None, []
        top = ttk.Frame(self)
        top.pack(fill='x', padx=6, pady=6)
        self.q = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.q)
        e.pack(side='left', fill='x', expand=True)
        e.focus_set()
        self.q.trace_add('write', lambda *a: self.fill())
        self.cat = tk.StringVar(value='Все')
        if categories:
            cb = ttk.Combobox(top, textvariable=self.cat, values=['Все'] + categories, state='readonly', width=18)
            cb.pack(side='left', padx=6)
            cb.bind('<<ComboboxSelected>>', lambda e: self.fill())
        body = ttk.PanedWindow(self, orient='horizontal')
        body.pack(fill='both', expand=True, padx=6)
        self.lb = tk.Listbox(body, exportselection=False)
        self.desc = tk.Text(body, wrap='word', width=40, state='disabled')
        body.add(self.lb, weight=3)
        body.add(self.desc, weight=2)
        bot = ttk.Frame(self)
        bot.pack(fill='x', padx=6, pady=6)
        ttk.Button(bot, text='Выбрать', command=self.ok).pack(side='right')
        ttk.Button(bot, text='Отмена', command=self.destroy).pack(side='right', padx=6)
        if allow_new:
            ttk.Button(bot, text=allow_new, command=self.new).pack(side='left')
        self.lb.bind('<Double-Button-1>', lambda e: self.ok())
        self.lb.bind('<<ListboxSelect>>', lambda e: self.show_desc())
        self.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.destroy())
        self.fill()
        self.grab_set()
        self.wait_window(self)

    def fill(self):
        q = self.q.get().lower()
        cat = self.cat.get()
        self.lb.delete(0, 'end')
        self.shown = []
        for it in self.items:
            key, text, desc, c = (list(it) + ['', ''])[:4]
            if cat != 'Все' and c != cat:
                continue
            if q and q not in text.lower() and q not in str(key).lower():
                continue
            self.shown.append(it)
            self.lb.insert('end', text)
        if self.shown:
            self.lb.selection_set(0)
            self.show_desc()

    def show_desc(self):
        sel = self.lb.curselection()
        self.desc.configure(state='normal')
        self.desc.delete('1.0', 'end')
        if sel:
            it = list(self.shown[sel[0]]) + ['', '']
            self.desc.insert('1.0', it[2] or '')
        self.desc.configure(state='disabled')

    def ok(self):
        sel = self.lb.curselection()
        if sel:
            self.result = self.shown[sel[0]][0]
            self.destroy()

    def new(self):
        self.result = '__new__'
        self.destroy()


class FormulaDialog(tk.Toplevel):
    """Редактор формулы: текст с проверкой, палитра функций/датчиков/переменных, дерево узлов."""

    def __init__(self, master, proj, title, text):
        super().__init__(master)
        self.title(title)
        self.geometry('980x600')
        self.transient(master)
        self.proj, self.result = proj, None
        pw = ttk.PanedWindow(self, orient='horizontal')
        pw.pack(fill='both', expand=True, padx=6, pady=6)
        left = ttk.Frame(pw)
        right = ttk.Frame(pw)
        pw.add(left, weight=3)
        pw.add(right, weight=2)
        ttk.Label(left, text='Выражение (переменные [имя], списки {имя}, датчики и функции — по имени, '
                             'аргументы через « ; »):', wraplength=560).pack(anchor='w')
        self.txt = tk.Text(left, height=7, wrap='word', font=('Consolas', 11))
        self.txt.pack(fill='x')
        self.txt.insert('1.0', text)
        self.txt.bind('<KeyRelease>', lambda e: self.check())
        self.status = ttk.Label(left, text='', foreground='#a00', wraplength=560)
        self.status.pack(anchor='w', pady=2)
        ops = ttk.Frame(left)
        ops.pack(fill='x')
        for sym in ['+', '-', '*', '/', '^', 'mod', '=', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not', '&', '( )']:
            ttk.Button(ops, text=sym, width=4, command=lambda s=sym: self.insert(s if s != '( )' else '()', s == '( )')).pack(side='left')
        ttk.Label(left, text='Структура (узлы XML):').pack(anchor='w', pady=(8, 0))
        self.tree = ttk.Treeview(left, columns=('type', 'value'), show='tree headings', height=8)
        self.tree.heading('#0', text='узел')
        self.tree.heading('type', text='type')
        self.tree.heading('value', text='value')
        self.tree.column('#0', width=150)
        self.tree.pack(fill='both', expand=True)
        # палитра
        r1 = ttk.Frame(right)
        r1.pack(fill='x')
        self.kind = tk.StringVar(value='Функции')
        cb = ttk.Combobox(r1, textvariable=self.kind, state='readonly', width=12,
                          values=['Функции', 'Датчики', 'Переменные', 'Списки'])
        cb.pack(side='left')
        cb.bind('<<ComboboxSelected>>', lambda e: self.fill())
        self.q = tk.StringVar()
        self.q.trace_add('write', lambda *a: self.fill())
        ttk.Entry(r1, textvariable=self.q).pack(side='left', fill='x', expand=True, padx=4)
        self.lb = tk.Listbox(right, exportselection=False)
        self.lb.pack(fill='both', expand=True, pady=4)
        self.lb.bind('<Double-Button-1>', lambda e: self.insert_selected())
        self.lb.bind('<<ListboxSelect>>', lambda e: self.show_help())
        self.help = tk.Text(right, height=6, wrap='word', state='disabled')
        self.help.pack(fill='x')
        ttk.Button(right, text='Вставить в позицию курсора', command=self.insert_selected).pack(fill='x', pady=4)
        bot = ttk.Frame(self)
        bot.pack(fill='x', padx=6, pady=6)
        ttk.Button(bot, text='Применить', command=self.ok).pack(side='right')
        ttk.Button(bot, text='Отмена', command=self.destroy).pack(side='right', padx=6)
        self.fill()
        self.check()
        self.txt.focus_set()
        self.grab_set()
        self.wait_window(self)

    def names(self):
        k = self.kind.get()
        if k == 'Функции':
            return list(C.FUNCTIONS)
        if k == 'Датчики':
            return list(C.SENSORS)
        if k == 'Переменные':
            return sorted({n for n, _, _ in self.proj.variables()})
        return sorted({n for n, _, _ in self.proj.lists()})

    def fill(self):
        q = self.q.get().lower()
        self.lb.delete(0, 'end')
        for n in self.names():
            if q in n.lower():
                self.lb.insert('end', n)

    def show_help(self):
        sel = self.lb.curselection()
        self.help.configure(state='normal')
        self.help.delete('1.0', 'end')
        if sel and self.kind.get() == 'Функции':
            h = C.FUNC_HELP.get(self.lb.get(sel[0]))
            if h:
                self.help.insert('1.0', 'Аргументы: %s\n%s' % (h[0], h[1]))
        self.help.configure(state='disabled')

    def insert(self, s, caret_inside=False):
        self.txt.insert('insert', s)
        if caret_inside:
            self.txt.mark_set('insert', 'insert-1c')
        self.txt.focus_set()
        self.check()

    def insert_selected(self):
        sel = self.lb.curselection()
        if not sel:
            return
        n, k = self.lb.get(sel[0]), self.kind.get()
        if k == 'Функции':
            self.insert(n + '()', True)
        elif k == 'Датчики':
            self.insert(('$' + n) if n in C.FUNCTIONS else n)
        elif k == 'Переменные':
            self.insert('[%s]' % n)
        else:
            self.insert('{%s}' % n)

    def check(self):
        self.tree.delete(*self.tree.get_children())
        try:
            n = parse_formula_text(self.txt.get('1.0', 'end').strip())
        except FormulaSyntaxError as e:
            self.status.configure(text=str(e))
            return None
        self.status.configure(text='')
        self.draw(n, '')
        return n

    def draw(self, n, parent, role=''):
        if n is None:
            return
        iid = self.tree.insert(parent, 'end', text=role or 'формула', values=(n.type, n.value or ''), open=True)
        if n.left is not None:
            self.draw(n.left, iid, 'leftChild')
        if n.right is not None:
            self.draw(n.right, iid, 'rightChild')
        for i, x in enumerate(n.extra):
            self.draw(x, iid, 'additional[%d]' % i)

    def ok(self):
        n = self.check()
        if n is None:
            messagebox.showerror('Формула', self.status.cget('text'), parent=self)
            return
        self.result = n
        self.destroy()


# ---------------------------------------------------------------------------
# Главное окно
# ---------------------------------------------------------------------------

class App:
    def __init__(self, master, path=None):
        self.master = master
        self.proj = Project.new()
        self.proj.dirty = False
        self.item2el, self.el2iid, self.res_items = {}, {}, {}
        self.pmap = {}
        self.cur = None
        self.clip = None          # ('copy'|'cut', элемент)
        self.photo = None
        ttk.Style().theme_use('clam') if 'clam' in ttk.Style().theme_names() else None
        self.build_menu()
        self.build_ui()
        master.protocol('WM_DELETE_WINDOW', self.on_close)
        for seq, fn in (('<Control-s>', self.save), ('<Control-o>', self.open), ('<Control-n>', self.new),
                        ('<Control-f>', self.find)):
            master.bind_all(seq, lambda e, f=fn: (f(), 'break')[1])
        if path:
            self.load(path)
        else:
            self.refresh_tree()
        self.update_title()

    # --- построение интерфейса
    def build_menu(self):
        m = tk.Menu(self.master)
        self.master.config(menu=m)

        def menu(label, items):
            mm = tk.Menu(m, tearoff=0)
            m.add_cascade(label=label, menu=mm)
            for it in items:
                if it is None:
                    mm.add_separator()
                else:
                    mm.add_command(label=it[0], command=it[1], accelerator=it[2] if len(it) > 2 else None)
            return mm
        menu('Файл', [('Новый проект…', self.new, 'Ctrl+N'), ('Открыть…', self.open, 'Ctrl+O'),
                      ('Сохранить', self.save, 'Ctrl+S'), ('Сохранить как…', self.save_as), None,
                      ('Экспорт code.xml…', self.export_xml), ('Файлы архива…', self.files_dialog), None,
                      ('Выход', self.on_close)])
        menu('Правка', [('Отменить', self.undo, 'Ctrl+Z'), ('Повторить', self.redo, 'Ctrl+Y'), None,
                        ('Копировать', self.copy, 'Ctrl+C'), ('Вырезать (переместить)', self.cut, 'Ctrl+X'),
                        ('Вставить', self.paste, 'Ctrl+V'), ('Дублировать', self.duplicate, 'Ctrl+D'),
                        ('Удалить', self.delete, 'Del'), None,
                        ('Переместить вверх', lambda: self.move(-1), 'Alt+↑'), ('Переместить вниз', lambda: self.move(1), 'Alt+↓'),
                        ('Отключить/включить блок', self.toggle_comment, 'Ctrl+E'), None,
                        ('Найти…', self.find, 'Ctrl+F')])
        menu('Добавить', [('Сцену', self.add_scene), ('Объект', self.add_object), ('Скрипт…', self.add_script),
                          ('Блок…', self.add_brick, 'Ins'), None, ('Образ из файла…', self.add_look),
                          ('Звук из файла…', self.add_sound), None, ('Переменную…', lambda: self.add_data('var')),
                          ('Список…', lambda: self.add_data('list'))])
        menu('Проект', [('Проверить проект', self.run_validate), ('Переменные и списки…', self.vars_dialog),
                        ('Удалить неиспользуемые файлы…', self.clean_files), None, ('О формате и синтаксисе формул', self.help_box)])

    def build_ui(self):
        tb = ttk.Frame(self.master)
        tb.pack(fill='x')
        for text, fn in (('Скрипт', self.add_script), ('Блок', self.add_brick), ('Объект', self.add_object),
                         ('▲', lambda: self.move(-1)), ('▼', lambda: self.move(1)), ('Откл/Вкл', self.toggle_comment),
                         ('Дублировать', self.duplicate), ('Удалить', self.delete), ('Проверить', self.run_validate)):
            ttk.Button(tb, text=text, command=fn).pack(side='left', padx=2, pady=2)
        self.status_var = tk.StringVar(value='Готово')
        ttk.Label(self.master, textvariable=self.status_var, relief='sunken', anchor='w').pack(side='bottom', fill='x')
        outer = ttk.PanedWindow(self.master, orient='vertical')
        outer.pack(fill='both', expand=True)
        top = ttk.PanedWindow(outer, orient='horizontal')
        outer.add(top, weight=5)
        lf = ttk.Frame(top)
        top.add(lf, weight=2)
        self.tree = ttk.Treeview(lf, show='tree', selectmode='browse')
        sb = ttk.Scrollbar(lf, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        self.tree.bind('<Button-3>', self.popup)
        self.tree.bind('<Button-2>', self.popup)
        for seq, fn in (('<Control-c>', self.copy), ('<Control-x>', self.cut), ('<Control-v>', self.paste),
                        ('<Control-d>', self.duplicate), ('<Delete>', self.delete), ('<Insert>', self.add_brick),
                        ('<Control-z>', self.undo), ('<Control-y>', self.redo), ('<Control-e>', self.toggle_comment),
                        ('<Alt-Up>', lambda: self.move(-1)), ('<Alt-Down>', lambda: self.move(1))):
            self.tree.bind(seq, lambda e, f=fn: (f(), 'break')[1])
        self.nb = ttk.Notebook(top)
        top.add(self.nb, weight=3)
        self.props = ScrollFrame(self.nb)
        self.nb.add(self.props, text='Свойства')
        xf = ttk.Frame(self.nb)
        self.nb.add(xf, text='XML')
        self.xml_text = tk.Text(xf, wrap='none', font=('Consolas', 10), undo=True)
        xs = ttk.Scrollbar(xf, orient='vertical', command=self.xml_text.yview)
        self.xml_text.configure(yscrollcommand=xs.set)
        bx = ttk.Frame(xf)
        bx.pack(side='bottom', fill='x')
        ttk.Button(bx, text='Применить XML к элементу', command=self.apply_xml).pack(side='left', padx=4, pady=3)
        xs.pack(side='right', fill='y')
        self.xml_text.pack(fill='both', expand=True)
        hf = ttk.Frame(self.nb)
        self.nb.add(hf, text='Справка')
        self.help_text = tk.Text(hf, wrap='word', state='disabled')
        self.help_text.pack(fill='both', expand=True)
        bf = ttk.Frame(outer)
        outer.add(bf, weight=1)
        self.res_label = ttk.Label(bf, text='Результаты проверки / поиска')
        self.res_label.pack(anchor='w')
        self.res = ttk.Treeview(bf, columns=('lvl', 'where', 'msg'), show='headings', height=6)
        for c, t, w in (('lvl', 'Уровень', 110), ('where', 'Где', 260), ('msg', 'Сообщение', 800)):
            self.res.heading(c, text=t)
            self.res.column(c, width=w, anchor='w')
        rs = ttk.Scrollbar(bf, orient='vertical', command=self.res.yview)
        self.res.configure(yscrollcommand=rs.set)
        self.res.pack(side='left', fill='both', expand=True)
        rs.pack(side='right', fill='y')
        self.res.bind('<Double-Button-1>', self.res_goto)

    # --- служебное
    def status(self, msg):
        self.status_var.set(msg)

    def update_title(self):
        name = os.path.basename(self.proj.path) if self.proj.path else 'без имени'
        self.master.title('%s%s — %s' % ('*' if self.proj.dirty else '', name, APP_TITLE))

    def confirm_discard(self):
        if not self.proj.dirty:
            return True
        r = messagebox.askyesnocancel(APP_TITLE, 'Сохранить изменения?')
        if r is None:
            return False
        if r:
            return self.save()
        return True

    def on_close(self):
        if self.confirm_discard():
            self.master.destroy()

    # --- файлы
    def new(self):
        if not self.confirm_discard():
            return
        name = simpledialog.askstring('Новый проект', 'Имя проекта:', initialvalue='Новый проект', parent=self.master)
        if not name:
            return
        self.proj = Project.new(name)
        self.proj.is_zip = True
        self.cur = None
        self.refresh_tree()
        self.update_title()

    def open(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(title='Открыть проект', filetypes=[
            ('Проекты NewCatroid', '*.newtrobat *.catrobat *.zip *.xml'), ('Все файлы', '*.*')])
        if p:
            self.load(p)

    def load(self, path):
        try:
            self.proj = Project.open(path)
        except Exception as e:
            messagebox.showerror('Ошибка открытия', '%s: %s' % (type(e).__name__, e))
            return
        self.cur = None
        self.refresh_tree()
        self.status('Открыт %s (%d файлов в архиве)' % (path, len(self.proj.files)))
        self.update_title()

    def save(self):
        if not self.proj.path:
            return self.save_as()
        return self._save(self.proj.path)

    def save_as(self):
        ext = '.newtrobat' if self.proj.is_zip else '.xml'
        p = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[('Проект', '*' + ext), ('Все файлы', '*.*')])
        return self._save(p) if p else False

    def _save(self, path):
        try:
            self.proj.save(path)
        except Exception as e:
            messagebox.showerror('Ошибка сохранения', '%s: %s' % (type(e).__name__, e))
            return False
        self.status('Сохранено: %s' % path)
        self.update_title()
        return True

    def export_xml(self):
        p = filedialog.asksaveasfilename(defaultextension='.xml', initialfile='code.xml')
        if p:
            self.proj.export_code_xml(p)
            self.status('code.xml сохранён: %s' % p)

    # --- модель дерева
    def kind(self, el):
        t = el.tag
        if t == 'program':
            return 'program'
        if t == 'scene':
            return 'scene'
        if is_object(el):
            return 'object'
        if is_script(el):
            return 'script'
        if is_brick(el):
            return 'brick'
        if t in ('look', 'sound'):
            return t
        if t == 'userVariable':
            return 'var'
        if t == 'userList':
            return 'ulist'
        if t == 'nfcTag':
            return 'nfc'
        if t in LIST_LABELS or t.endswith('Bricks') or t in ('scenes', 'objectList', 'scriptList', 'brickList'):
            return 'list'
        return 'other'

    def target(self, el):
        ref = el.get('reference')
        if ref is None:
            return el
        return resolve_ref(el, self.pmap, ref, self.proj.root)

    def data_name(self, el):
        t = self.target(el)
        if t is None:
            return '⚠ ссылка не найдена'
        n = t.find('.//name') if t.tag == 'userVariable' else t.find('name')
        if t.tag in ('look', 'sound'):
            return t.get('name', '?')
        return (n.text if n is not None else '?') or '?'

    def tree_children(self, el):
        k = self.kind(el)
        r = self.proj.root
        if k == 'program':
            out = [x for x in (child(r, 'header'), child(r, 'settings')) if x is not None]
            sc = child(r, 'scenes')
            out += list(sc) if sc is not None else []
            out += [x for x in (child(r, 'programVariableList'), child(r, 'programListOfLists'),
                                child(r, 'programMultiplayerVariableList')) if x is not None]
            return out
        if k == 'scene':
            ol = child(el, 'objectList')
            return list(ol) if ol is not None else []
        if k == 'object':
            sl = child(el, 'scriptList')
            out = list(sl) if sl is not None else []
            for t in ('lookList', 'soundList', 'userVariables', 'userLists', 'userDefinedBrickList', 'nfcTagList'):
                c = child(el, t)
                if c is not None:
                    out.append(c)
            return out
        if k == 'script':
            bl = child(el, 'brickList')
            return list(bl) if bl is not None else []
        if k == 'brick':
            return [c for c in el if c.tag.endswith('Bricks') and c.tag != 'elseIfBranches']
        if k == 'list':
            return list(el)
        return []

    def label(self, el):
        k = self.kind(el)
        if k == 'program':
            return 'Проект: ' + child_text(child(el, 'header'), 'programName', '?')
        if k == 'scene':
            return 'Сцена: ' + child_text(el, 'name', '?')
        if k == 'object':
            return '%s: %s' % (OBJECT_LABELS.get(el.get('type'), 'Объект'), el.get('name'))
        if k == 'script':
            off = ' (отключён)' if child_text(el, 'commentedOut') == 'true' else ''
            extra = ''
            if el.get('type') == 'BroadcastScript':
                extra = ' «%s»' % child_text(el, 'receivedMessage')
            return '▶ %s%s%s' % (script_title(el.get('type')), extra, off)
        if k == 'brick':
            return self.brick_label(el)
        if k in ('look', 'sound'):
            ref = ' →' if el.get('reference') is not None else ''
            return '%s: %s%s' % ('Образ' if k == 'look' else 'Звук', self.data_name(el), ref)
        if k == 'var':
            return 'Переменная: %s%s' % (self.data_name(el), ' (ссылка)' if el.get('reference') else '')
        if k == 'ulist':
            return 'Список: %s%s' % (self.data_name(el), ' (ссылка)' if el.get('reference') else '')
        if k == 'nfc':
            return 'NFC: %s' % child_text(el, 'name')
        if k == 'list':
            n = len([c for c in el])
            base = LIST_LABELS.get(el.tag, el.tag)
            if el.tag in ('scenes', 'objectList', 'scriptList', 'brickList'):
                return base
            return '%s (%d)' % (base, n) if el.tag not in ('loopBricks', 'ifBranchBricks', 'elseBranchBricks') else '↳ ' + base
        return '<%s>' % el.tag

    def brick_label(self, el):
        s = brick_title(el.get('type'))
        parts = []
        for f in get_formulas(el)[:4]:
            try:
                t = formula_text(f)
            except Exception:
                t = '?'
            parts.append(t if len(t) < 28 else t[:26] + '…')
        for tag in REF_TAGS:
            c = child(el, tag)
            if c is not None:
                parts.append('«%s»' % self.data_name(c))
        if parts:
            s += '  ( ' + ' ; '.join(parts) + ' )'
        if child_text(el, 'commentedOut') == 'true':
            s = '⊘ ' + s
        return s

    def refresh_tree(self, select=None, open_els=None):
        root = self.proj.root
        self.pmap = parent_map(root)
        if open_els is None:
            open_els = {el for iid, el in self.item2el.items() if self.tree.exists(iid) and self.tree.item(iid, 'open')}
        sel = select if select is not None else self.cur
        self.tree.delete(*self.tree.get_children())
        self.item2el, self.el2iid = {}, {}
        self.build_node('', root, open_els, True)
        if sel is not None:
            self.goto(sel)
        else:
            self.goto(root)

    def build_node(self, parent_iid, el, open_els, force_open=False):
        iid = self.tree.insert(parent_iid, 'end', text=self.label(el), open=(force_open or el in open_els))
        self.item2el[iid] = el
        self.el2iid[el] = iid
        for c in self.tree_children(el):
            self.build_node(iid, c, open_els, self.kind(c) in ('scene',) and el.tag == 'program')

    def relabel(self):
        self.pmap = parent_map(self.proj.root)
        for iid, el in self.item2el.items():
            self.tree.item(iid, text=self.label(el))

    def goto(self, el):
        pm = self.pmap
        while el is not None and el not in self.el2iid:
            el = pm.get(el)
        if el is None:
            return
        iid = self.el2iid[el]
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)
        self.on_select()

    def sel_el(self):
        s = self.tree.selection()
        return self.item2el.get(s[0]) if s else None

    def on_select(self, _=None):
        el = self.sel_el()
        self.cur = el
        if el is None:
            return
        self.show_props(el)
        self.show_xml(el)
        self.show_help(el)

    # --- выполнение правок
    def apply(self, fn, select=None, structural=True):
        self.pmap = parent_map(self.proj.root)
        open_els = {el for iid, el in self.item2el.items() if self.tree.exists(iid) and self.tree.item(iid, 'open')}
        try:
            with self.proj.edit() as g:
                fn(g)
        except Exception as e:
            messagebox.showerror('Ошибка правки', '%s: %s' % (type(e).__name__, e))
            self.refresh_tree()
            return False
        if self.proj.warnings:
            self.status('; '.join(self.proj.warnings))
        if structural:
            self.refresh_tree(select=select if select is not None else self.cur, open_els=open_els)
        else:
            self.relabel()
            self.after_edit_props()
        self.update_title()
        return True

    def after_edit_props(self):
        self.master.after_idle(lambda: self.cur is not None and self.show_props(self.cur))

    def undo(self):
        self.step_history(self.proj.undo)

    def redo(self):
        self.step_history(self.proj.redo)

    def step_history(self, fn):
        paths = {}
        for iid, el in self.item2el.items():
            if self.tree.exists(iid) and self.tree.item(iid, 'open'):
                paths[el] = None
        pm = self.pmap
        def path(el):
            out = []
            while el in pm:
                out.append(list(pm[el]).index(el))
                el = pm[el]
            return out[::-1]
        open_paths = [path(el) for el in paths if el in pm or el is self.proj.root]
        sel_path = path(self.cur) if self.cur is not None and self.cur in pm else []
        if not fn():
            self.status('Нечего отменять/повторять')
            return
        open_els = {self.proj.by_path(p) for p in open_paths}
        self.cur = None
        self.refresh_tree(select=self.proj.by_path(sel_path), open_els=open_els)
        self.update_title()

    # --- позиции вставки
    def container_for(self, kind, sel):
        """Возвращает (список-контейнер, индекс вставки) для создания элемента вида kind."""
        pm = self.pmap
        proj = self.proj
        def after(lst, item):
            if item is not None and item in pm and pm[item] is lst:
                return list(lst).index(item) + 1
            return len(lst)
        if kind == 'scene':
            lst = child(proj.root, 'scenes')
            return lst, after(lst, proj.scene_of(sel, pm) if sel is not None else None)
        if kind == 'object':
            sc = proj.scene_of(sel, pm) if sel is not None else None
            if sc is None:
                return None, 0
            lst = child(sc, 'objectList')
            return lst, after(lst, proj.object_of(sel, pm))
        ob = proj.object_of(sel, pm) if sel is not None else None
        if kind in ('script', 'look', 'sound'):
            if ob is None:
                return None, 0
            lst = child(ob, {'script': 'scriptList', 'look': 'lookList', 'sound': 'soundList'}[kind])
            return lst, after(lst, sel)
        if kind == 'brick':
            if sel is None:
                return None, 0
            k = self.kind(sel)
            if k == 'script':
                lst = child(sel, 'brickList')
                return lst, len(lst)
            if k == 'list' and (sel.tag.endswith('Bricks') or sel.tag == 'brickList'):
                return sel, len(sel)
            if k == 'brick':
                p = pm.get(sel)
                return p, after(p, sel)
            if k == 'list' and sel.tag == 'userDefinedBrickList':
                return sel, len(sel)
        return None, 0

    def add_scene(self):
        name = simpledialog.askstring('Новая сцена', 'Имя сцены:', parent=self.master)
        if not name:
            return
        lst, i = self.container_for('scene', self.cur)
        sc = make_scene(unique_name(name, {child_text(s, 'name') for s in lst}))
        self.apply(lambda g: lst.insert(i, sc), select=sc)

    def add_object(self):
        lst, i = self.container_for('object', self.cur)
        if lst is None:
            return self.status('Выберите сцену или объект')
        name = simpledialog.askstring('Новый объект', 'Имя объекта:', initialvalue='Объект', parent=self.master)
        if not name:
            return
        ob = make_object(unique_name(name, {o.get('name') for o in lst}))
        self.apply(lambda g: lst.insert(i, ob), select=ob)

    def add_script(self):
        lst, i = self.container_for('script', self.cur)
        if lst is None:
            return self.status('Выберите объект')
        items = []
        for st in C.SCRIPTS:
            items.append((st, '%s   [%s]' % (script_title(st), st), '', 'События'))
        key = Picker(self.master, 'Выберите скрипт (блок-шапку)', items).result
        if not key:
            return
        s = make_script(key)
        self.apply(lambda g: lst.insert(i, s), select=s)

    def add_brick(self):
        lst, i = self.container_for('brick', self.cur)
        if lst is None:
            return self.status('Выберите скрипт или блок, после которого вставить')
        items, cats = [], set()
        for bt, b in C.BLOCKS.items():
            if bt in C.HEADER_BRICKS or bt.endswith('Script'):
                continue
            desc = '%s\n\nТип: %s\nКатегория: %s\nПоля формул: %s\n\n%s' % (
                b['title'], bt, b['cat'], ', '.join(C.BRICK_FIELDS.get(bt, [])) or '—', b['purpose'])
            if b['params']:
                desc += '\n\nПараметры:\n' + '\n'.join('• %s (%s, по умолч. %s): %s' % tuple(p) for p in b['params'])
            items.append((bt, '%s   [%s]' % (b['title'], bt), desc, b['cat']))
            cats.add(b['cat'])
        items.sort(key=lambda x: (x[3], x[1]))
        key = Picker(self.master, 'Выберите блок', items, sorted(c for c in cats if c)).result
        if not key:
            return
        b = make_brick(key)
        ok = self.apply(lambda g: lst.insert(i, b), select=b)
        if ok:
            self.ask_refs_for_new_brick(b)

    def ask_refs_for_new_brick(self, b):
        bt = b.get('type')
        if bt in C.USERVAR_BRICKS:
            self.choose_ref(b, 'userVariable')
        if bt in C.USERLIST_BRICKS:
            self.choose_ref(b, 'userList')
        for tag, kinds in C.REF_FIELDS.items():
            if bt in kinds:
                self.choose_ref(b, tag)

    def add_look(self):
        self.add_media('look')

    def add_sound(self):
        self.add_media('sound')

    def add_media(self, kind):
        lst, i = self.container_for(kind, self.cur)
        if lst is None:
            return self.status('Выберите объект')
        types = [('Изображения', '*.png *.jpg *.jpeg *.gif *.webp *.bmp')] if kind == 'look' else [('Звуки', '*.wav *.mp3 *.ogg *.mid *.midi *.m4a')]
        paths = filedialog.askopenfilenames(title='Выберите файлы', filetypes=types + [('Все файлы', '*.*')])
        if not paths:
            return
        ob = self.proj.object_of(lst, self.pmap)
        scene = self.proj.scene_of(ob, self.pmap)
        added = []

        def fn(g):
            taken = {x.get('name') for x in lst}
            for p in paths:
                fname = self.proj.add_image(scene, p) if kind == 'look' else self.proj.add_sound(scene, p)
                nm = unique_name(os.path.splitext(os.path.basename(p))[0], taken)
                taken.add(nm)
                el = make_look(nm, fname) if kind == 'look' else make_sound(nm, fname)
                lst.insert(len(lst), el)
                added.append(el)
        self.apply(fn, select=added[-1] if added else None)

    def add_data(self, what):
        name = simpledialog.askstring('Новая ' + ('переменная' if what == 'var' else 'список'), 'Имя:', parent=self.master)
        if not name:
            return
        glob = messagebox.askyesno('Область', 'Сделать глобальной (для всего проекта)?\n«Нет» — локальная для выбранного объекта.')
        root = self.proj.root
        if glob:
            lst = child(root, 'programVariableList' if what == 'var' else 'programListOfLists')
        else:
            ob = self.proj.object_of(self.cur, self.pmap) if self.cur is not None else None
            if ob is None:
                return self.status('Выберите объект для локальной переменной')
            lst = child(ob, 'userVariables' if what == 'var' else 'userLists')
        el = make_variable(name) if what == 'var' else make_list(name)
        self.apply(lambda g: lst.append(el), select=el)

    # --- выбор ссылок (образ, звук, переменная, список, объект)
    def candidates(self, tag, owner):
        out = []
        pm = self.pmap
        proj = self.proj
        if tag in ('userVariable', 'userList'):
            seq = proj.variables() if tag == 'userVariable' else proj.lists()
            for n, el, scope in seq:
                out.append((el, '%s   [%s]' % (n, scope), '', ''))
        elif tag in ('look', 'sound'):
            sc = proj.scene_of(owner, pm)
            for ob in sc.iter('object') if sc is not None else []:
                for x in ob.iterfind('lookList/look' if tag == 'look' else 'soundList/sound'):
                    if x.get('reference') is None:
                        out.append((x, '%s / %s' % (ob.get('name'), x.get('name')), '', ''))
        else:
            sc = proj.scene_of(owner, pm)
            for ob in sc.iter('object') if sc is not None else []:
                out.append((ob, ob.get('name'), '', ''))
        return out

    def choose_ref(self, owner, tag):
        cands = self.candidates(tag, owner)
        keyed = [(str(i), t, d, c) for i, (el, t, d, c) in enumerate(cands)]
        allow_new = 'Создать новую…' if tag in ('userVariable', 'userList') else None
        res = Picker(self.master, 'Выберите: ' + tag, keyed, allow_new=allow_new).result
        if res is None:
            return
        pm = self.pmap
        new_def = None
        if res == '__new__':
            name = simpledialog.askstring('Новая', 'Имя:', parent=self.master)
            if not name:
                return
            glob = messagebox.askyesno('Область', 'Глобальная? («Нет» — локальная для объекта блока)')
            new_def = make_variable(name) if tag == 'userVariable' else make_list(name)
            if glob:
                holder = child(self.proj.root, 'programVariableList' if tag == 'userVariable' else 'programListOfLists')
            else:
                ob = self.proj.object_of(owner, pm)
                holder = child(ob, 'userVariables' if tag == 'userVariable' else 'userLists')
            target = new_def
        else:
            target = cands[int(res)][0]
        if tag in OBJ_REF_TAGS:
            pass

        def fn(g):
            if new_def is not None:
                holder.append(new_def)
            old = child(owner, tag)
            if old is not None:
                owner.remove(old)
            ref = ET.Element(tag, {'reference': '.'})
            pos = 0
            for i, c in enumerate(owner):
                if c.tag in ('brickId', 'commentedOut', 'formulaList'):
                    pos = i + 1
            owner.insert(pos, ref)
            g.setdefault(target, []).append(ref)
        self.apply(fn, select=owner)

    def clear_ref(self, owner, tag):
        c = child(owner, tag)
        if c is not None:
            self.apply(lambda g: owner.remove(c), select=owner)

    # --- операции над выбранным
    def kind_of_sel(self):
        el = self.cur
        return (self.kind(el) if el is not None else None)

    def removable(self, el):
        k = self.kind(el)
        return k in ('scene', 'object', 'script', 'brick', 'look', 'sound', 'var', 'ulist', 'nfc')

    def delete(self):
        el = self.cur
        if el is None or not self.removable(el):
            return self.status('Этот элемент удалить нельзя')
        par = self.pmap.get(el)
        if self.kind(el) == 'scene' and len(par) <= 1:
            return self.status('Нужна минимум одна сцена')
        nxt = par
        self.apply(lambda g: par.remove(el), select=nxt)

    def move(self, d):
        el = self.cur
        if el is None or el not in self.pmap:
            return
        par = self.pmap[el]
        lst = list(par)
        i = lst.index(el)
        j = i + d
        if not (0 <= j < len(lst)):
            return

        def fn(g):
            par.remove(el)
            par.insert(j, el)
        self.apply(fn, select=el)

    def toggle_comment(self):
        el = self.cur
        if el is None or self.kind(el) not in ('brick', 'script'):
            return
        c = child(el, 'commentedOut')
        if c is None:
            return
        self.apply(lambda g: setattr(c, 'text', 'false' if c.text == 'true' else 'true'), select=el, structural=False)

    def copy(self):
        if self.cur is not None and self.removable(self.cur):
            self.clip = ('copy', self.cur)
            self.status('Скопировано: %s' % self.label(self.cur))

    def cut(self):
        if self.cur is not None and self.removable(self.cur):
            self.clip = ('cut', self.cur)
            self.status('Вырезано (будет перемещено при вставке): %s' % self.label(self.cur))

    def paste(self):
        if self.clip is None:
            return
        mode, src = self.clip
        k = self.kind(src)
        kk = {'scene': 'scene', 'object': 'object', 'script': 'script', 'brick': 'brick', 'look': 'look', 'sound': 'sound'}.get(k)
        if kk is None:
            return self.status('Этот тип элементов вставлять нельзя')
        lst, i = self.container_for(kk, self.cur)
        if lst is None:
            return self.status('Сюда вставить нельзя: выберите подходящее место')
        if src in self.pmap and mode == 'cut':
            if any(a is src for a in self.ancestors(lst)) or lst is src:
                return self.status('Нельзя вставить элемент внутрь самого себя')

            def fn(g):
                old = self.pmap[src]
                idx = list(old).index(src)
                old.remove(src)
                j = i - 1 if old is lst and idx < i else i
                lst.insert(j, src)
            self.apply(fn, select=src)
            self.clip = None
        else:
            try:
                c, links = self.proj.clone(src)
            except Exception as e:
                return messagebox.showerror('Копирование', str(e))
            if kk == 'object':
                c.set('name', unique_name(c.get('name'), {o.get('name') for o in lst}))
            elif kk == 'scene':
                self.copy_scene_files(src, c, lst)
            elif kk in ('look', 'sound'):
                c.set('name', unique_name(c.get('name'), {o.get('name') for o in lst}))

            def fn(g):
                lst.insert(i, c)
                for cp, t in links:
                    g.setdefault(t, []).append(cp)
            self.apply(fn, select=c)

    def ancestors(self, el):
        out = []
        while el in self.pmap:
            el = self.pmap[el]
            out.append(el)
        return out

    def copy_scene_files(self, src, c, lst):
        name = unique_name(child_text(src, 'name'), {child_text(s, 'name') for s in lst})
        child(c, 'name').text = name
        od, nd = self.proj.scene_dir(src), self.proj.scene_dir(c)
        for k, v in list(self.proj.files.items()):
            if k.startswith(od + '/'):
                self.proj.files[nd + k[len(od):]] = v

    def duplicate(self):
        if self.cur is None or not self.removable(self.cur):
            return
        self.clip = ('copy', self.cur)
        self.paste()

    # --- панель свойств
    def show_props(self, el):
        self.pmap = parent_map(self.proj.root)
        pf = self.props
        pf.clear()
        f = pf.inner
        f.columnconfigure(1, weight=1)
        self.photo = None
        row = [0]
        k = self.kind(el)

        def head(text):
            ttk.Label(f, text=text, font=('TkDefaultFont', 10, 'bold'), wraplength=520).grid(
                row=row[0], column=0, columnspan=3, sticky='w', padx=4, pady=(8, 2))
            row[0] += 1

        def line(label, value, commit=None, values=None, width=None):
            ttk.Label(f, text=label, wraplength=170).grid(row=row[0], column=0, sticky='nw', padx=4, pady=2)
            var = tk.StringVar(value=value)
            if commit is None:
                ttk.Label(f, text=value, wraplength=360).grid(row=row[0], column=1, sticky='w', padx=4)
            else:
                w = (ttk.Combobox(f, textvariable=var, values=values) if values else ttk.Entry(f, textvariable=var))
                w.grid(row=row[0], column=1, sticky='ew', padx=4, pady=2)
                state = {'v': value}

                def do(_=None):
                    if var.get() != state['v']:
                        state['v'] = var.get()
                        commit(var.get())
                w.bind('<Return>', do)
                w.bind('<FocusOut>', do)
                if values:
                    w.bind('<<ComboboxSelected>>', do)
            row[0] += 1
            return var

        head(element_summary(el) if k != 'program' else 'Проект')
        # атрибуты
        if k == 'scene':
            line('Имя сцены', child_text(el, 'name'), lambda nv: self.set_text(el, 'name', nv))
        for a, v in list(el.attrib.items()):
            if a in ('reference', 'serialization'):
                continue
            ro = a.endswith('Id') or a == 'type' and k not in ('object',)
            vals = list(OBJECT_TYPES) if (a == 'type' and k == 'object') else None
            line(a, v, None if ro else (lambda nv, a=a: self.set_attr(el, a, nv)), values=vals)
        if el.get('reference') is not None:
            t = self.target(el)
            line('reference', el.get('reference'))
            line('→ указывает на', self.data_name(el) if t is not None else '⚠ не найдено')
        # служебные
        bid = child(el, 'brickId') or child(el, 'scriptId')
        if bid is not None:
            line(bid.tag, bid.text or '')
        co = child(el, 'commentedOut')
        if co is not None:
            cv = tk.BooleanVar(value=(co.text == 'true'))
            ttk.Checkbutton(f, text='Отключён (commentedOut)', variable=cv,
                            command=lambda: self.set_text(el, 'commentedOut', 'true' if cv.get() else 'false')).grid(
                row=row[0], column=0, columnspan=2, sticky='w', padx=4)
            row[0] += 1
        # формулы
        forms = get_formulas(el) if k in ('brick', 'script') else []
        if forms:
            head('Формулы')
            btype = el.get('type')
            names = C.BRICK_FIELDS.get(btype, [])
            params = C.BLOCKS.get(btype, {}).get('params', [])
            for fe in forms:
                key = formula_key(fe)
                lab = key
                if names and len(params) == len(names) and key in names:
                    lab = '%s\n(%s)' % (params[names.index(key)][0], key)
                try:
                    txt = formula_text(fe)
                except Exception:
                    txt = '?'
                ttk.Label(f, text=lab, wraplength=170).grid(row=row[0], column=0, sticky='nw', padx=4, pady=2)
                e = ttk.Entry(f)
                e.insert(0, txt)
                e.configure(state='readonly')
                e.grid(row=row[0], column=1, sticky='ew', padx=4, pady=2)
                ttk.Button(f, text='Изменить…', command=lambda fe=fe: self.edit_formula(el, fe)).grid(row=row[0], column=2, padx=4)
                row[0] += 1
            missing = [c for c in names if c not in {formula_key(x) for x in forms}]
            if missing:
                cb = ttk.Combobox(f, values=missing, state='readonly')
                cb.grid(row=row[0], column=1, sticky='ew', padx=4, pady=2)
                ttk.Button(f, text='+ поле', command=lambda cb=cb: cb.get() and self.apply(
                    lambda g: set_formula(el, cb.get(), None), select=el, structural=False)).grid(row=row[0], column=2, padx=4)
                row[0] += 1
        # ссылки (образ/звук/переменная/список/объект)
        if k in ('brick', 'script'):
            reftags = [t for t in REF_TAGS + OBJ_REF_TAGS if child(el, t) is not None]
            bt = el.get('type')
            if bt in C.USERVAR_BRICKS and 'userVariable' not in reftags:
                reftags.append('userVariable')
            if bt in C.USERLIST_BRICKS and 'userList' not in reftags:
                reftags.append('userList')
            for tag, kinds in C.REF_FIELDS.items():
                if bt in kinds and tag not in reftags:
                    reftags.append(tag)
            if reftags:
                head('Ссылки')
            for tag in reftags:
                c = child(el, tag)
                ttk.Label(f, text=tag).grid(row=row[0], column=0, sticky='nw', padx=4, pady=2)
                ttk.Label(f, text=(self.data_name(c) if c is not None else '— не выбрано —'), wraplength=300).grid(
                    row=row[0], column=1, sticky='w', padx=4)
                bf = ttk.Frame(f)
                bf.grid(row=row[0], column=2, padx=4)
                ttk.Button(bf, text='Выбрать…', command=lambda tag=tag: self.choose_ref(el, tag)).pack(side='left')
                if c is not None:
                    ttk.Button(bf, text='✕', width=2, command=lambda tag=tag: self.clear_ref(el, tag)).pack(side='left')
                row[0] += 1
        # простые поля
        leaves = [c for c in el if not len(c) and not c.attrib and c.tag not in HIDDEN_LEAVES and not (k == 'scene' and c.tag == 'name')
                  and not c.tag.endswith('Bricks') and c.tag not in ('lookList', 'soundList', 'scriptList', 'brickList',
                                                                      'nfcTagList', 'userVariables', 'userLists',
                                                                      'userDefinedBrickList', 'objectList', 'scenes',
                                                                      'formulaList', 'formulaMap', 'additionalChildren',
                                                                      'settings', 'userDefinedBrickDataList',
                                                                      'userDefinedBrickInputs')
                  and not (c.tag in ('programVariableList', 'programListOfLists', 'programMultiplayerVariableList'))]
        if leaves:
            head('Параметры' if k != 'program' else 'Параметры проекта')
            for c in leaves:
                vals = ['true', 'false'] if (c.text in ('true', 'false')) else None
                line(c.tag, c.text or '', (lambda nv, c=c: self.set_text(el, c.tag, nv)), values=vals)
        if k in ('var', 'ulist'):
            t = self.target(el)
            nm = t.find('.//name') if t is not None else None
            if nm is not None:
                line('Имя', nm.text or '', lambda nv, t=t, nm=nm, tag=k: self.rename_data(t, nm, nv, tag))
        if k == 'look':
            self.look_preview(el, f, row)
        if k == 'program':
            head('Файлов в архиве: %d' % len(self.proj.files))

    def look_preview(self, el, f, row):
        t = self.target(el)
        if t is None:
            return
        sc = self.proj.scene_of(el, self.pmap)
        key = '%s/images/%s' % (self.proj.scene_dir(sc), t.get('fileName')) if sc is not None else None
        data = self.proj.files.get(key)
        if data is None:
            ttk.Label(f, text='Файл образа не найден в архиве: %s' % key, foreground='#a00', wraplength=500).grid(
                row=row[0], column=0, columnspan=3, padx=4, pady=4, sticky='w')
            row[0] += 1
            return
        try:
            img = tk.PhotoImage(data=base64.b64encode(data))
            k = max(1, max(img.width(), img.height()) // 260)
            if k > 1:
                img = img.subsample(k, k)
            self.photo = img
            ttk.Label(f, image=img).grid(row=row[0], column=0, columnspan=3, padx=4, pady=6, sticky='w')
        except Exception:
            ttk.Label(f, text='(предпросмотр недоступен для этого формата)').grid(row=row[0], column=0, columnspan=3, sticky='w', padx=4)
        row[0] += 1

    def set_attr(self, el, a, v):
        if el.tag == 'object' and a == 'name':
            sc = self.proj.scene_of(el, self.pmap)
            if v in object_names_excl(sc, el):
                return messagebox.showerror('Имя занято', 'В сцене уже есть объект «%s»' % v)
        self.apply(lambda g: el.set(a, v), select=el, structural=True)

    def set_text(self, el, tag, v):
        if el.tag == 'scene' and tag == 'name':
            return self.apply(lambda g: self.proj.rename_scene(el, v), select=el)

        def fn(g):
            c = child(el, tag)
            if c is None:
                c = ET.SubElement(el, tag)
            c.text = v
        self.apply(fn, select=el, structural=True)

    def rename_data(self, target, nm, new, tag):
        old = nm.text

        def fn(g):
            nm.text = new
            n = rename_in_formulas(self.proj.root, 'USER_VARIABLE' if tag == 'var' else 'USER_LIST', old, new)
            self.status('Переименовано; обновлено узлов формул: %d' % n)
        self.apply(fn, select=self.cur)

    def edit_formula(self, owner, fe):
        key_attr = 'category' if fe.get('category') is not None else 'input'
        key = fe.get(key_attr)
        dlg = FormulaDialog(self.master, self.proj, 'Формула: %s — %s' % (brick_title(owner.get('type', '')), key),
                            formula_text(fe))
        if dlg.result is None:
            return
        self.apply(lambda g: set_formula(owner, key, dlg.result, key_attr), select=owner, structural=False)

    # --- XML и справка
    def show_xml(self, el):
        self.xml_text.delete('1.0', 'end')
        if self.kind(el) in ('program', 'scene') or el.tag in ('scenes',):
            self.xml_text.insert('1.0', '<!-- элемент слишком крупный: выберите объект, скрипт или блок. '
                                        'Полный code.xml: Файл → Экспорт code.xml -->')
            return
        s = element_xml(el)
        self.xml_text.insert('1.0', s if len(s) < 400000 else s[:400000] + '\n<!-- обрезано -->')

    def apply_xml(self):
        el = self.cur
        if el is None or el not in self.pmap or el is self.proj.root:
            return
        try:
            new = parse_xml(self.xml_text.get('1.0', 'end').strip())
        except ET.ParseError as e:
            return messagebox.showerror('XML', 'Ошибка разбора: %s' % e)
        par = self.pmap[el]

        def fn(g):
            i = list(par).index(el)
            par[i] = new
            retarget_groups(g, el, new)
        self.apply(fn, select=new)

    def show_help(self, el):
        t = self.help_text
        t.configure(state='normal')
        t.delete('1.0', 'end')
        txt = ''
        k = self.kind(el)
        if k == 'brick':
            bt = el.get('type')
            b = C.BLOCKS.get(bt)
            if b:
                txt = '%s\nТип: %s   Категория: %s\nПоля формул: %s\n\n%s\n' % (
                    b['title'], bt, b['cat'], ', '.join(C.BRICK_FIELDS.get(bt, [])) or '—', b['purpose'])
                for p in b['params']:
                    txt += '\n• %s (%s, по умолчанию %s): %s' % tuple(p)
        elif k == 'script':
            st = el.get('type')
            for hb, sc in C.HEADER_BRICKS.items():
                if sc == st and hb in C.BLOCKS:
                    b = C.BLOCKS[hb]
                    txt = '%s (%s)\n\n%s' % (b['title'], st, b['purpose'])
        t.insert('1.0', txt or 'Нет справки для этого элемента.')
        t.configure(state='disabled')

    def help_box(self):
        win = tk.Toplevel(self.master)
        win.title('Справка')
        win.geometry('720x560')
        t = tk.Text(win, wrap='word')
        t.pack(fill='both', expand=True)
        t.insert('1.0', HELP_TEXT)
        t.configure(state='disabled')

    # --- проверка, поиск, результаты
    def show_results(self, title, rows):
        self.res.delete(*self.res.get_children())
        self.res_items = {}
        self.pmap = parent_map(self.proj.root)
        self.res_label.configure(text=title)
        for lvl, el, msg in rows:
            iid = self.res.insert('', 'end', values=(lvl, self.where(el), msg))
            self.res_items[iid] = el

    def where(self, el):
        parts = []
        e = el
        while e is not None:
            if self.kind(e) in ('scene', 'object', 'script', 'brick'):
                parts.append(self.label(e).split('  (')[0])
            e = self.pmap.get(e)
        return ' › '.join(reversed(parts[:3])) or '<%s>' % el.tag

    def run_validate(self):
        res = validate(self.proj)
        order = {'ОШИБКА': 0, 'ПРЕДУПРЕЖДЕНИЕ': 1, 'ИНФО': 2}
        res.sort(key=lambda r: order.get(r[0], 3))
        self.show_results('Проверка: %d сообщений (ошибок %d)' % (len(res), sum(1 for r in res if r[0] == 'ОШИБКА')), res)
        self.status('Проверка завершена: %d сообщений' % len(res))

    def find(self):
        q = simpledialog.askstring('Поиск', 'Что найти (в атрибутах, тексте, формулах):', parent=self.master)
        if not q:
            return
        found = search(self.proj.root, q)
        self.show_results('Найдено: %d' % len(found), [('найдено', el, what) for el, what in found[:500]])

    def res_goto(self, _=None):
        s = self.res.selection()
        if s and s[0] in self.res_items:
            self.pmap = parent_map(self.proj.root)
            self.goto(self.res_items[s[0]])

    # --- переменные, файлы
    def vars_dialog(self):
        items = []
        for n, el, scope in self.proj.variables():
            items.append(('v%d' % len(items), 'Переменная  %s   [%s]' % (n, scope), '', ''))
        for n, el, scope in self.proj.lists():
            items.append(('l%d' % len(items), 'Список  %s   [%s]' % (n, scope), '', ''))
        Picker(self.master, 'Переменные и списки проекта (двойной щелчок — закрыть)', items or [('-', '(нет)', '', '')])

    def files_dialog(self):
        win = tk.Toplevel(self.master)
        win.title('Файлы архива')
        win.geometry('640x460')
        lb = tk.Listbox(win, selectmode='extended')
        lb.pack(fill='both', expand=True, padx=6, pady=6)

        def fill():
            lb.delete(0, 'end')
            for n, b in self.proj.files.items():
                lb.insert('end', '%s    (%d Б)' % (n, len(b)))

        def names():
            keys = list(self.proj.files)
            return [keys[i] for i in lb.curselection()]

        def extract():
            for n in names():
                d = filedialog.asksaveasfilename(initialfile=os.path.basename(n), parent=win)
                if d:
                    with open(d, 'wb') as f:
                        f.write(self.proj.files[n])

        def add():
            p = filedialog.askopenfilename(parent=win)
            if not p:
                return
            arc = simpledialog.askstring('Путь в архиве', 'Имя записи (например files/hf.rscene):',
                                         initialvalue='files/' + os.path.basename(p), parent=win)
            if arc:
                with open(p, 'rb') as f:
                    self.proj.add_file(arc, f.read())
                fill()
                self.update_title()

        def delete():
            for n in names():
                del self.proj.files[n]
            self.proj.dirty = True
            fill()
            self.update_title()
        bf = ttk.Frame(win)
        bf.pack(fill='x', pady=4)
        for t, c in (('Извлечь…', extract), ('Добавить…', add), ('Удалить', delete)):
            ttk.Button(bf, text=t, command=c).pack(side='left', padx=4)
        fill()

    def clean_files(self):
        un = unused_files(self.proj)
        if not un:
            return messagebox.showinfo('Файлы', 'Неиспользуемых файлов образов/звуков нет.')
        if messagebox.askyesno('Удалить файлы', 'Неиспользуемых файлов: %d\n\n%s\n\nУдалить?' % (len(un), '\n'.join(un[:15]))):
            for n in un:
                del self.proj.files[n]
            self.proj.dirty = True
            self.update_title()

    # --- контекстное меню
    def popup(self, ev):
        iid = self.tree.identify_row(ev.y)
        if iid:
            self.tree.selection_set(iid)
            self.on_select()
        m = tk.Menu(self.master, tearoff=0)
        for t, c in (('Добавить блок…', self.add_brick), ('Добавить скрипт…', self.add_script), ('Добавить объект', self.add_object),
                     None, ('Копировать', self.copy), ('Вырезать', self.cut), ('Вставить', self.paste), ('Дублировать', self.duplicate),
                     None, ('Вверх', lambda: self.move(-1)), ('Вниз', lambda: self.move(1)),
                     ('Отключить/включить', self.toggle_comment), None, ('Удалить', self.delete)):
            if t is None:
                m.add_separator()
            else:
                m.add_command(label=t, command=c)
        m.tk_popup(ev.x_root, ev.y_root)


def object_names_excl(scene_el, el):
    ol = child(scene_el, 'objectList') if scene_el is not None else []
    return {o.get('name') for o in ol if o is not el}


HELP_TEXT = """РЕДАКТОР code.xml для NewCatroid (.newtrobat)

Слева — структура проекта: сцены → объекты → скрипты → блоки. Справа — свойства выбранного элемента,
его XML (можно править вручную и применять) и справка по блоку из документации.

ГОРЯЧИЕ КЛАВИШИ (в дереве): Ins — добавить блок, Del — удалить, Ctrl+C/X/V — копировать/переместить/вставить,
Ctrl+D — дублировать, Ctrl+E — отключить/включить блок, Alt+↑/↓ — переместить, Ctrl+Z/Y — отмена/повтор,
Ctrl+S — сохранить, Ctrl+F — поиск.

ССЫЛКИ XSTREAM. Образы, звуки, переменные и списки в code.xml хранятся как определение (первое вхождение)
и ссылки reference="../../…" на него. Редактор пересчитывает эти пути сам при вставке, удалении, переносе
и копировании. Если удалить определение, его роль переходит к следующей ссылке.

СИНТАКСИС ФОРМУЛ
  числа            12   0.5
  строки           "текст"
  переменная       [имя]           (USER_VARIABLE)
  список           {имя}           (USER_LIST)
  датчик           FPS  или  $FPS  (SENSOR)
  функция          RAND(1; 10)     (FUNCTION; аргументы через «;» или «,»)
  вход польз.блока @имя            (USER_DEFINED_BRICK_INPUT)
  операторы        + - * / ^ mod = != < > <= >= and or not &   (и/или/не, ≤ ≥ ≠ × ÷ тоже понимаются)
  скобки           ( ... )         (узел BRACKET)
Функции с тремя и более аргументами записываются в additionalChildren автоматически.
Список имён функций и датчиков — в палитре справа в окне формулы.

ПРОВЕРКА (меню «Проект»): допустимые type блоков и скриптов, category формул (неизвестная category
ломает загрузку в приложении), порядок ссылок, дубли идентификаторов, наличие файлов образов и звуков.
"""


def main():
    root = tk.Tk()
    root.geometry('1360x820')
    App(root, sys.argv[1] if len(sys.argv) > 1 else None)
    root.mainloop()


if __name__ == '__main__':
    main()
