#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
newtrobat_cli — консольный редактор code.xml проектов NewCatroid (.newtrobat).

Режимы:
  python newtrobat_cli.py проект.newtrobat                     интерактивная оболочка
  python newtrobat_cli.py проект.newtrobat -c "tree -d 3"      разовые команды (-c можно повторять)
  python newtrobat_cli.py проект.newtrobat -f script.txt -w    команды из файла, затем сохранить (-w)
  python newtrobat_cli.py проект.newtrobat -c validate         код выхода 2, если есть ошибки

Адреса элементов — номера в дереве, как их печатает `tree`: «1.2.1» = 1-й ребёнок проекта → 2-й → 1-й.
`.` — текущий элемент (меняется командой `cd`), `..` — его родитель, `/` — корень проекта.
Команда `help` печатает список команд.
"""
import argparse
import difflib
import os
import shlex
import sys
import xml.etree.ElementTree as ET

import newtrobat_catalog as C
from newtrobat_core import (
    FormulaSyntaxError, Project, brick_title, child, child_text, element_summary, element_xml, formula_key,
    formula_text, get_formulas, is_brick, is_object, is_script, make_brick, make_list, make_look, make_object,
    make_scene, make_script, make_sound, make_variable, node_to_text, parent_map, parse_formula_text, parse_xml,
    retarget_groups, script_title, search, set_formula, unique_name, unused_files, validate, OBJECT_TYPES,
    rename_in_formulas, resolve_ref,
)

LIST_LABELS = {
    'loopBricks': 'Тело', 'ifBranchBricks': 'Тогда', 'elseBranchBricks': 'Иначе', 'nestedBricks': 'Вложенные блоки',
    'threadBricks': 'Поток', 'tryBricks': 'try', 'catchBricks': 'catch', 'finallyBricks': 'finally',
    'lookList': 'Образы', 'soundList': 'Звуки', 'userVariables': 'Локальные переменные',
    'userLists': 'Локальные списки', 'userDefinedBrickList': 'Пользовательские блоки', 'nfcTagList': 'NFC-метки',
    'programVariableList': 'Глобальные переменные', 'programListOfLists': 'Глобальные списки',
    'programMultiplayerVariableList': 'Переменные мультиплеера', 'settings': 'Настройки', 'header': 'Заголовок',
}
HIDDEN = {'brickId', 'scriptId', 'commentedOut'}
STRUCT = {'lookList', 'soundList', 'scriptList', 'brickList', 'nfcTagList', 'userVariables', 'userLists',
          'userDefinedBrickList', 'objectList', 'scenes', 'formulaList', 'formulaMap', 'additionalChildren',
          'settings', 'userDefinedBrickDataList', 'userDefinedBrickInputs', 'programVariableList',
          'programListOfLists', 'programMultiplayerVariableList'}


class CliError(Exception):
    pass


class Cli:
    def __init__(self):
        self.proj = Project.new()
        self.proj.dirty = False
        self.cwd = None
        self.addr = {}
        self.byaddr = {}
        self.pmap = {}
        self.reindex()

    # ------------------------------------------------------------------ дерево
    def kind(self, el):
        t = el.tag
        if t in ('program', 'scene'):
            return t
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
        if t in ('header', 'settings'):
            return 'other'
        if t in LIST_LABELS or t.endswith('Bricks') or t in ('scenes', 'objectList', 'scriptList', 'brickList'):
            return 'list'
        return 'other'

    def tree_children(self, el):
        k, r = self.kind(el), self.proj.root
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
            out += [c for c in (child(el, t) for t in ('lookList', 'soundList', 'userVariables', 'userLists',
                                                       'userDefinedBrickList', 'nfcTagList')) if c is not None]
            return out
        if k == 'script':
            bl = child(el, 'brickList')
            return list(bl) if bl is not None else []
        if k == 'brick':
            return [c for c in el if c.tag.endswith('Bricks') and c.tag != 'elseIfBranches']
        if k == 'list':
            return list(el)
        return []

    def reindex(self):
        root = self.proj.root
        self.pmap = parent_map(root)
        self.addr, self.byaddr = {}, {}

        def walk(el, a):
            self.addr[el] = a
            self.byaddr[a] = el
            for i, c in enumerate(self.tree_children(el), 1):
                walk(c, (a + '.' if a else '') + str(i))
        walk(root, '')
        if self.cwd is not None and self.cwd not in self.addr:
            self.cwd = None

    def a(self, el):
        a = self.addr.get(el)
        return '?' if a is None else (a or '/')

    def data_name(self, el):
        t = el
        if el.get('reference') is not None:
            t = resolve_ref(el, self.pmap, el.get('reference'), self.proj.root)
        if t is None:
            return '⚠ ссылка не найдена'
        if t.tag in ('look', 'sound'):
            return t.get('name', '?')
        n = t.find('.//name')
        return (n.text if n is not None else '?') or '?'

    def label(self, el):
        k = self.kind(el)
        if k == 'program':
            return 'Проект: ' + child_text(child(el, 'header'), 'programName', '?')
        if k == 'scene':
            return 'Сцена: ' + child_text(el, 'name', '?')
        if k == 'object':
            return '%s: %s' % ({'GroupSprite': 'Группа', 'GroupItemSprite': 'Элемент группы'}.get(el.get('type'), 'Объект'), el.get('name'))
        if k == 'script':
            off = ' (отключён)' if child_text(el, 'commentedOut') == 'true' else ''
            extra = ' «%s»' % child_text(el, 'receivedMessage') if el.get('type') == 'BroadcastScript' else ''
            return '▶ %s [%s]%s%s' % (script_title(el.get('type')), el.get('type'), extra, off)
        if k == 'brick':
            s = brick_title(el.get('type'))
            parts = []
            for f in get_formulas(el)[:4]:
                try:
                    t = formula_text(f)
                except Exception:
                    t = '?'
                parts.append(t if len(t) < 30 else t[:28] + '…')
            for tag in ('look', 'sound', 'userVariable', 'userList'):
                c = child(el, tag)
                if c is not None:
                    parts.append('«%s»' % self.data_name(c))
            if parts:
                s += ' ( ' + ' ; '.join(parts) + ' )'
            return ('⊘ ' if child_text(el, 'commentedOut') == 'true' else '') + s
        if k in ('look', 'sound'):
            return '%s: %s%s' % ('Образ' if k == 'look' else 'Звук', self.data_name(el), ' →' if el.get('reference') else '')
        if k == 'var':
            return 'Переменная: %s%s' % (self.data_name(el), ' (ссылка)' if el.get('reference') else '')
        if k == 'ulist':
            return 'Список: %s%s' % (self.data_name(el), ' (ссылка)' if el.get('reference') else '')
        if k == 'nfc':
            return 'NFC: ' + child_text(el, 'name')
        if k == 'list':
            return '%s (%d)' % (LIST_LABELS.get(el.tag, el.tag), len(el))
        if el.tag in LIST_LABELS:
            return LIST_LABELS[el.tag]
        return '<%s>' % el.tag

    # ------------------------------------------------------------------ адреса
    def resolve(self, s=None):
        if s is None or s == '.':
            return self.cwd if self.cwd is not None else self.proj.root
        if s == '/' or s == '':
            return self.proj.root
        if s == '..':
            cur = self.cwd if self.cwd is not None else self.proj.root
            par = self.pmap.get(cur)
            # родитель в терминах дерева
            for el, a in self.addr.items():
                if cur in self.tree_children(el):
                    return el
            return par or cur
        if s in self.byaddr:
            return self.byaddr[s]
        raise CliError('Нет элемента с адресом «%s» (посмотрите `tree`)' % s)

    def container_for(self, kind, sel):
        pm = self.pmap
        proj = self.proj

        def after(lst, item):
            if item is not None and item in pm and pm[item] is lst:
                return list(lst).index(item) + 1
            return len(lst)
        if kind == 'scene':
            lst = child(proj.root, 'scenes')
            return lst, after(lst, proj.scene_of(sel, pm))
        if kind == 'object':
            sc = proj.scene_of(sel, pm)
            if sc is None:
                raise CliError('Для объекта укажите сцену или объект (cd/--at)')
            lst = child(sc, 'objectList')
            return lst, after(lst, proj.object_of(sel, pm))
        if kind in ('script', 'look', 'sound'):
            ob = proj.object_of(sel, pm)
            if ob is None:
                raise CliError('Выберите объект (cd АДРЕС_ОБЪЕКТА или --at)')
            lst = child(ob, {'script': 'scriptList', 'look': 'lookList', 'sound': 'soundList'}[kind])
            return lst, after(lst, sel)
        if kind == 'brick':
            k = self.kind(sel)
            if k == 'script':
                lst = child(sel, 'brickList')
                return lst, len(lst)
            if k == 'list' and (sel.tag.endswith('Bricks') or sel.tag in ('brickList', 'userDefinedBrickList')):
                return sel, len(sel)
            if k == 'brick':
                p = pm.get(sel)
                return p, after(p, sel)
        raise CliError('Сюда нельзя вставить элемент вида «%s» (выберите скрипт, блок или тело блока)' % kind)

    # ------------------------------------------------------------------ правки
    def edit(self, fn, msg=None):
        self.pmap = parent_map(self.proj.root)
        with self.proj.edit() as g:
            fn(g)
        for w in self.proj.warnings:
            print('! ' + w)
        self.reindex()
        if msg:
            print(msg)

    def resolve_type(self, name, pool, what):
        if name in pool:
            return name
        low = {p.lower(): p for p in pool}
        if name.lower() in low:
            return low[name.lower()]
        if what == 'brick' and name.lower() + 'brick' in low:
            return low[name.lower() + 'brick']
        hits = [t for t in pool if name.lower() in (brick_title(t) if what == 'brick' else script_title(t)).lower()
                or name.lower() in t.lower()]
        exact = [t for t in hits if t.lower() in (name.lower() + 'brick', name.lower() + 'script')]
        hits = exact or hits
        if len(hits) == 1:
            return hits[0]
        sug = hits[:8] or difflib.get_close_matches(name, list(pool), 6)
        raise CliError('Неизвестный %s «%s».%s' % (what, name, ' Похожие: ' + ', '.join(sug) if sug else ''))

    def find_data(self, tag, name, owner, local=False, create=True):
        seq = self.proj.variables() if tag == 'userVariable' else self.proj.lists()
        for n, el, scope in seq:
            if n == name:
                return el, None
        if not create:
            raise CliError('Нет «%s»' % name)
        new = make_variable(name) if tag == 'userVariable' else make_list(name)
        if local:
            ob = self.proj.object_of(owner, self.pmap)
            holder = child(ob, 'userVariables' if tag == 'userVariable' else 'userLists')
        else:
            holder = child(self.proj.root, 'programVariableList' if tag == 'userVariable' else 'programListOfLists')
        return new, holder

    def set_ref(self, owner, tag, target, g):
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

    def find_media(self, tag, name, owner):
        sc = self.proj.scene_of(owner, self.pmap)
        for x in sc.iter(tag):
            if x.get('reference') is None and x.get('name') == name:
                return x
        raise CliError('Не найден %s «%s» в сцене' % ('образ' if tag == 'look' else 'звук', name))

    # ------------------------------------------------------------------ команды
    def run(self, line):
        line = line.strip()
        if not line or line.startswith('#'):
            return
        try:
            argv = shlex.split(line)
        except ValueError as e:
            raise CliError('Ошибка разбора строки: %s' % e)
        cmd, args = argv[0].lower(), argv[1:]
        fn = getattr(self, 'c_' + cmd.replace('-', '_'), None)
        if fn is None:
            raise CliError('Неизвестная команда «%s». Список: help' % cmd)
        fn(args)

    def need(self, args, n, usage):
        if len(args) < n:
            raise CliError('Использование: ' + usage)

    def c_help(self, args):
        print(HELP)

    def c_open(self, args):
        self.need(args, 1, 'open ФАЙЛ')
        self.load(args[0])

    def load(self, path):
        try:
            self.proj = Project.open(path)
        except Exception as e:
            raise CliError('Не удалось открыть: %s: %s' % (type(e).__name__, e))
        self.cwd = None
        self.reindex()
        print('Открыт %s (файлов в архиве: %d)' % (path, len(self.proj.files)))

    def c_new(self, args):
        self.proj = Project.new(args[0] if args else 'Новый проект')
        self.cwd = None
        self.reindex()
        print('Создан новый проект (сохраните: save ФАЙЛ.newtrobat)')

    def c_save(self, args):
        path = args[0] if args else self.proj.path
        if not path:
            raise CliError('Укажите файл: save ФАЙЛ')
        self.proj.save(path)
        print('Сохранено: ' + path)

    def c_export(self, args):
        self.need(args, 1, 'export code.xml')
        self.proj.export_code_xml(args[0])
        print('Записан ' + args[0])

    def c_quit(self, args):
        raise EOFError

    c_exit = c_q = c_quit

    def c_pwd(self, args):
        el = self.resolve('.')
        print('%s  %s' % (self.a(el), self.label(el)))

    def c_cd(self, args):
        el = self.resolve(args[0] if args else '/')
        self.cwd = None if el is self.proj.root else el
        self.c_pwd([])

    def c_tree(self, args):
        depth, addr = 99, None
        it = iter(args)
        for x in it:
            if x in ('-d', '--depth'):
                depth = int(next(it, '3'))
            else:
                addr = x
        start = self.resolve(addr)

        def walk(el, d, ind):
            print('%s%-9s %s' % ('  ' * ind, self.a(el) or '/', self.label(el)))
            if d > 0:
                for c in self.tree_children(el):
                    walk(c, d - 1, ind + 1)
        walk(start, depth, 0)

    c_ls = c_tree

    def c_show(self, args):
        el = self.resolve(args[0] if args else None)
        print('%s   [адрес %s, <%s>]' % (element_summary(el), self.a(el), el.tag))
        for k, v in el.attrib.items():
            print('  @%s = %s' % (k, v))
        if el.get('reference') is not None:
            print('  → указывает на: ' + self.data_name(el))
        forms = get_formulas(el)
        if forms:
            print('  Формулы:')
            for f in forms:
                print('    %-28s %s' % (formula_key(f), formula_text(f)))
        bt = el.get('type')
        miss = [c for c in C.BRICK_FIELDS.get(bt, []) if c not in {formula_key(f) for f in forms}]
        if miss:
            print('  Не заданы поля формул (formula CAT …): ' + ', '.join(miss))
        for c in el:
            if c.tag in HIDDEN or c.tag in STRUCT or c.tag.endswith('Bricks'):
                continue
            if c.get('reference') is not None or c.tag in ('look', 'sound', 'userVariable', 'userList'):
                print('  %s → %s' % (c.tag, self.data_name(c)))
            elif not len(c):
                print('  %s = %s' % (c.tag, c.text or ''))
        for hid in ('brickId', 'scriptId'):
            if child(el, hid) is not None:
                print('  %s = %s' % (hid, child(el, hid).text))

    def c_xml(self, args):
        print(element_xml(self.resolve(args[0] if args else None)))

    def c_set(self, args):
        self.need(args, 3, 'set АДРЕС ИМЯ ЗНАЧЕНИЕ   (атрибут или простое поле)')
        el, name, val = self.resolve(args[0]), args[1], ' '.join(args[2:])
        if el.tag == 'scene' and name == 'name':
            if val in {child_text(x, 'name') for x in self.proj.scenes() if x is not el}:
                raise CliError('Сцена «%s» уже есть' % val)
            return self.edit(lambda g: self.proj.rename_scene(el, val), 'Сцена переименована (каталог в архиве перенесён)')
        if name in el.attrib and name != 'reference':
            if el.tag == 'object' and name == 'name':
                sc = self.proj.scene_of(el, self.pmap)
                if val in {o.get('name') for o in child(sc, 'objectList') if o is not el}:
                    raise CliError('Имя объекта «%s» уже занято' % val)
            self.edit(lambda g: el.set(name, val), '%s@%s = %s' % (self.a(el), name, val))
            return

        def fn(g):
            c = child(el, name)
            if c is None:
                c = ET.SubElement(el, name)
            c.text = val
        self.edit(fn, '%s.%s = %s' % (self.a(el), name, val))

    def c_formula(self, args):
        self.need(args, 3, 'formula АДРЕС КАТЕГОРИЯ ВЫРАЖЕНИЕ')
        el, cat, expr = self.resolve(args[0]), args[1], ' '.join(args[2:])
        try:
            node = parse_formula_text(expr)
        except FormulaSyntaxError as e:
            raise CliError('Формула: %s' % e)
        allowed = C.BRICK_FIELDS.get(el.get('type'))
        key = 'category'
        if any(f.get('input') == cat for f in get_formulas(el)):
            key = 'input'
        elif cat not in C.BRICKFIELDS:
            raise CliError('«%s» нет среди BrickField — приложение не загрузит такой проект' % cat)
        elif allowed is not None and cat not in allowed:
            print('! предупреждение: у блока %s допустимы поля: %s' % (el.get('type'), ', '.join(allowed)))
        self.edit(lambda g: set_formula(el, cat, node, key), '%s %s = %s' % (self.a(el), cat, node_to_text(node)))

    def parse_opts(self, args, flags_with_value, multi=()):
        pos, opts = [], {}
        it = iter(args)
        for x in it:
            if x.startswith('--'):
                name = x[2:]
                if name in flags_with_value:
                    v = next(it, None)
                    if v is None:
                        raise CliError('Опции --%s нужно значение' % name)
                    if name in multi:
                        opts.setdefault(name, []).append(v)
                    else:
                        opts[name] = v
                else:
                    opts[name] = True
            else:
                pos.append(x)
        return pos, opts

    def c_add(self, args):
        self.need(args, 1, 'add scene|object|script|brick|look|sound|var|list ... (help add)')
        what, rest = args[0].lower(), args[1:]
        pos, o = self.parse_opts(rest, {'at', 'set', 'var', 'list', 'look', 'sound', 'name'}, multi=('set',))
        sel = self.resolve(o.get('at'))
        if what == 'scene':
            self.need(pos, 1, 'add scene ИМЯ')
            lst, i = self.container_for('scene', sel)
            sc = make_scene(unique_name(pos[0], {child_text(s, 'name') for s in lst}))
            return self.edit(lambda g: lst.insert(i, sc), 'Добавлена сцена')
        if what == 'object':
            self.need(pos, 1, 'add object ИМЯ [--at АДРЕС]')
            lst, i = self.container_for('object', sel)
            ob = make_object(unique_name(pos[0], {x.get('name') for x in lst}))
            return self.edit(lambda g: lst.insert(i, ob), 'Добавлен объект')
        if what == 'script':
            self.need(pos, 1, 'add script ТИП|название  (например StartScript или "При запуске")')
            st = self.resolve_type(pos[0], C.SCRIPTS, 'script')
            lst, i = self.container_for('script', sel)
            s = make_script(st)
            return self.edit(lambda g: lst.insert(i, s), 'Добавлен скрипт %s' % st)
        if what == 'brick':
            self.need(pos, 1, 'add brick ТИП [--at АДРЕС] [--set КАТЕГОРИЯ=выражение] [--var имя] [--list имя] [--look имя] [--sound имя]')
            bt = self.resolve_type(pos[0], [t for t in C.BLOCKS if t not in C.HEADER_BRICKS], 'brick')
            lst, i = self.container_for('brick', sel)
            b = make_brick(bt)
            sets = []
            for s in o.get('set', []):
                if '=' not in s:
                    raise CliError('--set ожидает КАТЕГОРИЯ=выражение')
                cat, expr = s.split('=', 1)
                try:
                    sets.append((cat.strip(), parse_formula_text(expr)))
                except FormulaSyntaxError as e:
                    raise CliError('Формула «%s»: %s' % (expr, e))
            local = 'local' in o

            def fn(g):
                lst.insert(i, b)
                self.pmap = parent_map(self.proj.root)
                for cat, node in sets:
                    set_formula(b, cat, node)
                for tag, opt in (('userVariable', 'var'), ('userList', 'list')):
                    if opt in o:
                        target, holder = self.find_data(tag, o[opt], b, local)
                        if holder is not None:
                            holder.append(target)
                        self.set_ref(b, tag, target, g)
                for tag in ('look', 'sound'):
                    if tag in o:
                        self.set_ref(b, tag, self.find_media(tag, o[tag], b), g)
            self.edit(fn, 'Добавлен блок %s (%s)' % (brick_title(bt), bt))
            if bt in C.USERVAR_BRICKS and 'var' not in o:
                print('  подсказка: блоку нужна переменная — повторите с --var ИМЯ или `ref АДРЕС var ИМЯ`')
            return
        if what in ('look', 'sound'):
            self.need(pos, 1, 'add %s ФАЙЛ [--name ИМЯ] [--at АДРЕС_ОБЪЕКТА]' % what)
            lst, i = self.container_for(what, sel)
            sc = self.proj.scene_of(lst, self.pmap)
            path = pos[0]
            if not os.path.isfile(path):
                raise CliError('Нет файла ' + path)

            def fn(g):
                fname = self.proj.add_image(sc, path) if what == 'look' else self.proj.add_sound(sc, path)
                nm = unique_name(o.get('name') or os.path.splitext(os.path.basename(path))[0], {x.get('name') for x in lst})
                lst.insert(i, make_look(nm, fname) if what == 'look' else make_sound(nm, fname))
            return self.edit(fn, 'Добавлен %s из %s' % ('образ' if what == 'look' else 'звук', path))
        if what in ('var', 'list'):
            self.need(pos, 1, 'add %s ИМЯ [--local --at АДРЕС_ОБЪЕКТА]' % what)
            tag = 'userVariable' if what == 'var' else 'userList'
            el = make_variable(pos[0]) if what == 'var' else make_list(pos[0])
            if 'local' in o:
                ob = self.proj.object_of(sel, self.pmap)
                if ob is None:
                    raise CliError('Для локальной укажите объект: --at АДРЕС')
                holder = child(ob, 'userVariables' if what == 'var' else 'userLists')
            else:
                holder = child(self.proj.root, 'programVariableList' if what == 'var' else 'programListOfLists')
            return self.edit(lambda g: holder.append(el), 'Добавлена %s %s' % ('переменная' if what == 'var' else 'список', pos[0]))
        raise CliError('Неизвестный вид «%s»' % what)

    def c_ref(self, args):
        self.need(args, 3, 'ref АДРЕС_БЛОКА var|list|look|sound ИМЯ [--local]')
        el = self.resolve(args[0])
        kind, name = args[1], args[2]
        tag = {'var': 'userVariable', 'list': 'userList', 'look': 'look', 'sound': 'sound'}.get(kind)
        if tag is None:
            raise CliError('Вид: var, list, look или sound')

        def fn(g):
            if tag in ('userVariable', 'userList'):
                target, holder = self.find_data(tag, name, el, '--local' in args)
                if holder is not None:
                    holder.append(target)
            else:
                target = self.find_media(tag, name, el)
            self.set_ref(el, tag, target, g)
        self.edit(fn, '%s → %s' % (tag, name))

    def removable(self, el):
        return self.kind(el) in ('scene', 'object', 'script', 'brick', 'look', 'sound', 'var', 'ulist', 'nfc')

    def c_rm(self, args):
        self.need(args, 1, 'rm АДРЕС [АДРЕС…]')
        els = [self.resolve(a) for a in args]
        for el in els:
            if not self.removable(el):
                raise CliError('Элемент %s удалить нельзя' % self.a(el))

        def fn(g):
            for el in els:
                par = self.pmap.get(el)
                if par is not None and el in list(par):
                    par.remove(el)
        self.edit(fn, 'Удалено элементов: %d' % len(els))
    c_del = c_rm

    def paste_kind(self, src):
        k = self.kind(src)
        if k not in ('scene', 'object', 'script', 'brick', 'look', 'sound'):
            raise CliError('Этот тип элементов копировать/переносить нельзя')
        return k

    def c_cp(self, args):
        self.need(args, 2, 'cp АДРЕС КУДА   (вставка после КУДА или внутрь контейнера)')
        src, dst = self.resolve(args[0]), self.resolve(args[1])
        k = self.paste_kind(src)
        lst, i = self.container_for(k, dst)
        c, links = self.proj.clone(src)
        if k in ('object', 'look', 'sound'):
            c.set('name', unique_name(c.get('name'), {x.get('name') for x in lst}))
        if k == 'scene':
            name = unique_name(child_text(src, 'name'), {child_text(s, 'name') for s in lst})
            child(c, 'name').text = name
            od, nd = self.proj.scene_dir(src), self.proj.scene_dir(c)
            for fk, v in list(self.proj.files.items()):
                if fk.startswith(od + '/'):
                    self.proj.files[nd + fk[len(od):]] = v

        def fn(g):
            lst.insert(i, c)
            for cp, t in links:
                g.setdefault(t, []).append(cp)
        self.edit(fn, 'Скопировано')

    def c_mv(self, args):
        self.need(args, 2, 'mv АДРЕС КУДА')
        src, dst = self.resolve(args[0]), self.resolve(args[1])
        k = self.paste_kind(src)
        lst, i = self.container_for(k, dst)
        if lst is src or any(x is src for x in self.ancestors(lst)):
            raise CliError('Нельзя переместить элемент внутрь самого себя')

        def fn(g):
            old = self.pmap[src]
            idx = list(old).index(src)
            old.remove(src)
            lst.insert(i - 1 if old is lst and idx < i else i, src)
        self.edit(fn, 'Перемещено')

    def ancestors(self, el):
        out = []
        while el in self.pmap:
            el = self.pmap[el]
            out.append(el)
        return out

    def move(self, args, d):
        self.need(args, 1, 'up|down АДРЕС [N]')
        el = self.resolve(args[0])
        n = int(args[1]) if len(args) > 1 else 1
        par = self.pmap.get(el)
        if par is None:
            raise CliError('Этот элемент переместить нельзя')
        j = max(0, min(len(par) - 1, list(par).index(el) + d * n))

        def fn(g):
            par.remove(el)
            par.insert(j, el)
        self.edit(fn, 'Перемещено')

    def c_up(self, args):
        self.move(args, -1)

    def c_down(self, args):
        self.move(args, 1)

    def c_toggle(self, args):
        self.need(args, 1, 'toggle АДРЕС   (отключить/включить блок или скрипт)')
        el = self.resolve(args[0])
        c = child(el, 'commentedOut')
        if c is None:
            raise CliError('У элемента нет commentedOut')
        self.edit(lambda g: setattr(c, 'text', 'false' if c.text == 'true' else 'true'),
                  '%s: commentedOut = %s' % (self.a(el), 'false' if c.text == 'true' else 'true'))

    def c_rename(self, args):
        self.need(args, 3, 'rename var|list СТАРОЕ_ИМЯ НОВОЕ_ИМЯ   (имена в формулах обновятся)')
        kind, old, new = args[0], args[1], args[2]
        if kind not in ('var', 'list'):
            raise CliError('Вид: var или list')
        seq = self.proj.variables() if kind == 'var' else self.proj.lists()
        hit = [el for n, el, sc in seq if n == old]
        if not hit:
            raise CliError('Нет такой %s «%s» (команда vars)' % ('переменной' if kind == 'var' else 'списка', old))
        nm = hit[0].find('.//name')

        def fn(g):
            nm.text = new
            n = rename_in_formulas(self.proj.root, 'USER_VARIABLE' if kind == 'var' else 'USER_LIST', old, new)
            print('Обновлено узлов в формулах: %d' % n)
        self.edit(fn, '«%s» → «%s»' % (old, new))

    def c_replacexml(self, args):
        self.need(args, 2, 'replacexml АДРЕС ФАЙЛ.xml   (заменить элемент XML из файла)')
        el = self.resolve(args[0])
        par = self.pmap.get(el)
        if par is None:
            raise CliError('Корень заменить нельзя')
        with open(args[1], 'rb') as f:
            new = parse_xml(f.read())

        def fn(g):
            par[list(par).index(el)] = new
            retarget_groups(g, el, new)
        self.edit(fn, 'Элемент заменён')

    def c_undo(self, args):
        print('Отменено' if self.proj.undo() else 'Нечего отменять')
        self.reindex()

    def c_redo(self, args):
        print('Повторено' if self.proj.redo() else 'Нечего повторять')
        self.reindex()

    def c_find(self, args):
        self.need(args, 1, 'find ТЕКСТ')
        found = search(self.proj.root, ' '.join(args))
        seen = 0
        for el, what in found[:300]:
            e = el
            while e is not None and e not in self.addr:
                e = self.pmap.get(e)
            print('%-9s %-40s %s' % (self.a(e), self.label(e)[:40], what))
            seen += 1
        print('Найдено: %d%s' % (len(found), ' (показано 300)' if len(found) > 300 else ''))

    def c_validate(self, args):
        res = validate(self.proj)
        order = {'ОШИБКА': 0, 'ПРЕДУПРЕЖДЕНИЕ': 1, 'ИНФО': 2}
        res.sort(key=lambda r: order.get(r[0], 3))
        errs = 0
        for lvl, el, msg in res:
            e = el
            while e is not None and e not in self.addr:
                e = self.pmap.get(e)
            print('%-14s %-9s %s' % (lvl, self.a(e), msg))
            errs += lvl == 'ОШИБКА'
        print('Итого: %d сообщений, ошибок: %d' % (len(res), errs))
        self.last_errors = errs

    def c_files(self, args):
        for n, b in self.proj.files.items():
            print('%8d  %s' % (len(b), n))
        un = unused_files(self.proj)
        if un:
            print('Неиспользуемые: ' + ', '.join(un))

    def c_extract(self, args):
        self.need(args, 2, 'extract ЗАПИСЬ_АРХИВА ФАЙЛ')
        if args[0] not in self.proj.files:
            raise CliError('Нет такой записи (files)')
        with open(args[1], 'wb') as f:
            f.write(self.proj.files[args[0]])
        print('Записано ' + args[1])

    def c_put(self, args):
        self.need(args, 2, 'put ФАЙЛ ЗАПИСЬ_АРХИВА')
        with open(args[0], 'rb') as f:
            self.proj.add_file(args[1], f.read())
        print('Добавлено в архив: ' + args[1])

    def c_clean(self, args):
        un = unused_files(self.proj)
        for n in un:
            del self.proj.files[n]
        self.proj.dirty = True
        print('Удалено неиспользуемых файлов: %d' % len(un))

    def c_vars(self, args):
        for n, el, scope in self.proj.variables():
            print('переменная  %-30s %s' % (n, scope))
        for n, el, scope in self.proj.lists():
            print('список      %-30s %s' % (n, scope))

    def c_blocks(self, args):
        q = ' '.join(args).lower()
        n = 0
        for t, b in sorted(C.BLOCKS.items(), key=lambda kv: (kv[1]['cat'], kv[0])):
            if t in C.HEADER_BRICKS:
                continue
            if q and q not in t.lower() and q not in b['title'].lower() and q not in b['cat'].lower():
                continue
            print('%-14s %-40s %s' % (b['cat'][:14], t, b['title']))
            n += 1
        print('Блоков: %d' % n)

    def c_info(self, args):
        self.need(args, 1, 'info ТИП_БЛОКА|СКРИПТА|ФУНКЦИЯ')
        name = args[0]
        if name in C.FUNC_HELP or name in C.FUNCTIONS:
            h = C.FUNC_HELP.get(name, ['?', ''])
            return print('Функция %s(%s)\n  %s' % (name, h[0], h[1]))
        if name in C.SENSORS:
            return print('Датчик ' + name)
        if name in C.SCRIPTS:
            hb = [h for h, s in C.HEADER_BRICKS.items() if s == name]
            b = C.BLOCKS.get(hb[0]) if hb else None
            return print('Скрипт %s: %s\n  %s' % (name, script_title(name), b['purpose'] if b else ''))
        bt = self.resolve_type(name, list(C.BLOCKS), 'brick')
        b = C.BLOCKS[bt]
        print('%s [%s], категория: %s\nПоля формул: %s\n%s' % (
            b['title'], bt, b['cat'], ', '.join(C.BRICK_FIELDS.get(bt, [])) or '—', b['purpose']))
        for p in b['params']:
            print('  • %s (%s, по умолч. %s): %s' % tuple(p))

    def c_functions(self, args):
        q = ' '.join(args).upper()
        for f in C.FUNCTIONS:
            if q in f:
                h = C.FUNC_HELP.get(f)
                print('%-28s %s' % (f, ('(%s)' % h[0]) if h else ''))

    def c_sensors(self, args):
        q = ' '.join(args).upper()
        print('\n'.join(s for s in C.SENSORS if q in s))

    def c_scripts(self, args):
        for s in C.SCRIPTS:
            print('%-40s %s' % (s, script_title(s)))


HELP = """Команды (адреса — как в `tree`; `.` текущий, `..` родитель, `/` корень):
  open ФАЙЛ | new [ИМЯ] | save [ФАЙЛ] | export code.xml | quit
  tree [АДРЕС] [-d ГЛУБИНА]   дерево с адресами        pwd / cd АДРЕС   текущий элемент
  show [АДРЕС]                свойства, формулы, ссылки    xml [АДРЕС]   XML элемента
  set АДРЕС ИМЯ ЗНАЧЕНИЕ      атрибут или простое поле      formula АДРЕС КАТЕГОРИЯ ВЫРАЖЕНИЕ
  add scene ИМЯ | object ИМЯ | script ТИП | look ФАЙЛ | sound ФАЙЛ | var ИМЯ | list ИМЯ   (опции: --at АДРЕС, --local, --name)
  add brick ТИП [--at АДРЕС] [--set КАТЕГОРИЯ=выражение]... [--var ИМЯ] [--list ИМЯ] [--look ИМЯ] [--sound ИМЯ]
  ref АДРЕС var|list|look|sound ИМЯ     задать переменную/список/образ/звук блока
  rm АДРЕС…   cp АДРЕС КУДА   mv АДРЕС КУДА   up|down АДРЕС [N]   toggle АДРЕС   rename var|list СТАРОЕ НОВОЕ
  replacexml АДРЕС ФАЙЛ.xml   undo | redo
  find ТЕКСТ    validate    vars    files | extract ЗАПИСЬ ФАЙЛ | put ФАЙЛ ЗАПИСЬ | clean
  blocks [ЗАПРОС]  scripts  functions [ЗАПРОС]  sensors [ЗАПРОС]  info ТИП|ФУНКЦИЯ   справочник из документации
Типы блоков и скриптов можно писать по-русски (часть названия), если совпадение одно.
Формулы: числа, "строки", [переменная], {список}, ДАТЧИК, ФУНКЦИЯ(a; b), @вход, + - * / ^ mod = != < > <= >= and or not &, ( )
Пример: add brick Wait --at 1.3.1.2 --set TIME_TO_WAIT_IN_SECONDS="[t] * 2"
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description='Консольный редактор code.xml (.newtrobat)')
    ap.add_argument('file', nargs='?', help='проект .newtrobat / code.xml')
    ap.add_argument('-c', '--command', action='append', default=[], help='выполнить команду (можно несколько раз)')
    ap.add_argument('-f', '--script', help='файл с командами (по одной в строке, # — комментарий)')
    ap.add_argument('-w', '--write', action='store_true', help='сохранить проект после команд')
    ap.add_argument('-k', '--keep-going', action='store_true', help='не прерываться при ошибке команды')
    ns = ap.parse_args(argv)
    cli = Cli()
    cli.last_errors = 0
    try:
        if ns.file:
            cli.load(ns.file)
    except CliError as e:
        print('Ошибка: %s' % e, file=sys.stderr)
        return 1
    cmds = list(ns.command)
    if ns.script:
        with open(ns.script, encoding='utf-8') as f:
            cmds += f.read().splitlines()
    if cmds or ns.write:
        rc = 0
        for line in cmds:
            try:
                cli.run(line)
            except CliError as e:
                print('Ошибка: %s' % e, file=sys.stderr)
                rc = 1
                if not ns.keep_going:
                    return rc
            except EOFError:
                break
        if ns.write:
            try:
                cli.c_save([])
            except (CliError, OSError) as e:
                print('Ошибка сохранения: %s' % e, file=sys.stderr)
                return 1
        return rc or (2 if cli.last_errors else 0)
    # интерактивный режим
    try:
        import readline  # noqa: F401  (история и стрелки, если доступно)
    except ImportError:
        pass
    print('NewTrobat CLI. `help` — список команд, `quit` — выход.')
    while True:
        try:
            mark = '*' if cli.proj.dirty else ''
            line = input('%s%s> ' % (mark, cli.a(cli.resolve('.'))))
        except (EOFError, KeyboardInterrupt):
            print()
            line = 'quit'
        try:
            cli.run(line)
        except CliError as e:
            print('Ошибка: %s' % e)
        except EOFError:
            if cli.proj.dirty:
                ans = input('Есть несохранённые изменения. Сохранить? [y/n/отмена=c] ').strip().lower()
                if ans == 'c':
                    continue
                if ans == 'y':
                    try:
                        cli.c_save([])
                    except CliError as e:
                        print('Ошибка: %s' % e)
                        continue
            return 0
        except Exception as e:
            print('Внутренняя ошибка: %s: %s' % (type(e).__name__, e))


if __name__ == '__main__':
    sys.exit(main())
