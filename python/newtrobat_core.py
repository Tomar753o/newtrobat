# -*- coding: utf-8 -*-
"""
newtrobat_core — ядро редактора code.xml для NewCatroid (.newtrobat).

Не зависит от tkinter, поэтому его можно использовать и из скриптов:

    from newtrobat_core import Project
    p = Project.open("игра.newtrobat")
    with p.edit():
        ...                      # любые правки p.root
    p.save()

Что умеет:
  * читать/писать архив .newtrobat/.catrobat/.zip (остальные файлы архива сохраняются как есть)
    или отдельный code.xml;
  * правильно вести ссылки XStream (`reference="../../…"`) при вставке, удалении, переносе, копировании;
  * шаблоны скриптов/блоков/объектов/сцен по каталогу из документации;
  * формулы: дерево <-> текст, разбор выражений;
  * проверка проекта по правилам спецификации (validate).
"""
import contextlib
import copy
import io
import os
import re
import shutil
import uuid
import zipfile
import xml.etree.ElementTree as ET

import newtrobat_catalog as C

XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
BRICK_PKG = 'org.catrobat.catroid.content.bricks.'
SCRIPT_PKG = 'org.catrobat.catroid.content.'
FORMULA_ELEMENT = 'org.catrobat.catroid.formulaeditor.FormulaElement'
CURRENT_LANGUAGE_VERSION = 1.18
OBJECT_TYPES = ('Sprite', 'GroupSprite', 'GroupItemSprite')

ID_ATTRS = ('spriteId', 'sceneId', 'lookId', 'soundId')
ID_TAGS = ('brickId', 'scriptId')
STRING_FIELDS = {
    'VARIABLE', 'NOTE', 'SPEAK', 'STRING', 'ASK_QUESTION', 'NFC_NDEF_MESSAGE', 'ASK_SPEECH_QUESTION',
    'LIST_ADD_ITEM', 'INSERT_ITEM_INTO_USERLIST_VALUE', 'REPLACE_ITEM_IN_USERLIST_VALUE',
    'TEXT', 'NAME', 'TOAST', 'URL', 'FILE', 'FILE_NAME', 'FILENAME', 'KEY', 'MESSAGE', 'TITLE', 'HEADER',
    'BODY', 'QUESTION', 'SHOWTEXT', 'SOUND_NAME', 'WRITE_FILENAME', 'READ_FILENAME', 'CODE', 'DATA', 'HTML',
    'REGEX', 'FILE_URL', 'OPEN_URL', 'PROJECT_NAME', 'TABLE_NAME', 'SPRITE', 'CLONE_NAME', 'OBJECT_NAME',
    'INSTANCE_NAME', 'HINT_TEXT',
}
SYMBOLIC_DEFAULTS = {'ALIGNMENT_STYLE_CENTERED': '1', 'ALIGNMENT_STYLE_LEFT': '0', 'ALIGNMENT_STYLE_RIGHT': '2'}


def new_uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# XML: разбор и запись
# ---------------------------------------------------------------------------

def _clean(el):
    """Убирает отступы между элементами; текст листьев не трогает."""
    if len(el):
        if el.text is not None and not el.text.strip():
            el.text = None
        for c in el:
            _clean(c)
            if c.tail is not None and not c.tail.strip():
                c.tail = None


def parse_xml(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    root = ET.fromstring(data)
    _clean(root)
    return root


def serialize_xml(root):
    r = copy.deepcopy(root)
    ET.indent(r, space='  ')
    body = ET.tostring(r, encoding='unicode', short_empty_elements=True)
    body = body.replace(' />', '/>')
    return (XML_DECL + body + '\n').encode('utf-8')


def element_xml(el):
    r = copy.deepcopy(el)
    r.tail = None
    ET.indent(r, space='  ')
    return ET.tostring(r, encoding='unicode').replace(' />', '/>')


def parent_map(root):
    return {c: p for p in root.iter() for c in p}


def encode_dir_name(name):
    """Кодирование имени сцены для имени каталога (6.33)."""
    if name in ('.', '..'):
        return name.replace('.', '%2E')
    table = {'%': '%25', '"': '%22', '/': '%2F', ':': '%3A', '<': '%3C', '>': '%3E', '?': '%3F', '\\': '%5C', '|': '%7C'}
    return ''.join(table.get(ch, ch) for ch in name)


# ---------------------------------------------------------------------------
# Ссылки XStream (reference="../..")
# ---------------------------------------------------------------------------

_CHUNK = re.compile(r'^(.+?)(?:\[(\d+)\])?$')


def resolve_ref(elem, pmap, path, root=None):
    """Находит элемент, на который указывает reference. Контекст — сам элемент-ссылка."""
    cur = elem
    chunks = [c for c in path.split('/')]
    if path.startswith('/'):
        if root is None:
            return None
        chunks = chunks[1:]
        if not chunks or chunks[0].split('[')[0] != root.tag:
            return None
        cur = root
        chunks = chunks[1:]
    for ch in chunks:
        if ch in ('', '.'):
            continue
        if ch == '..':
            cur = pmap.get(cur)
            if cur is None:
                return None
            continue
        m = _CHUNK.match(ch)
        name, idx = m.group(1), int(m.group(2) or 1)
        same = [c for c in cur if c.tag == name]
        if idx > len(same):
            return None
        cur = same[idx - 1]
    return cur


def _chunks(el, pmap):
    out = []
    while el in pmap:
        p = pmap[el]
        idx = 1
        for s in p:
            if s is el:
                break
            if s.tag == el.tag:
                idx += 1
        out.append((el.tag, idx))
        el = p
    out.append((el.tag, 1))
    out.reverse()
    return out


def make_ref_path(src, dst, pmap):
    a, b = _chunks(src, pmap), _chunks(dst, pmap)
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    parts = ['..'] * (len(a) - i)
    for tag, idx in b[i:]:
        parts.append(tag if idx == 1 else '%s[%d]' % (tag, idx))
    return '/'.join(parts) if parts else '.'


def collect_groups(root):
    """{целевой элемент: [элементы-ссылки в порядке документа]}."""
    pmap = parent_map(root)
    groups = {}
    for el in root.iter():
        ref = el.get('reference')
        if ref is None:
            continue
        t = resolve_ref(el, pmap, ref, root)
        if t is not None and t is not el:
            groups.setdefault(t, []).append(el)
    return groups


def _become_reference(el):
    for c in list(el):
        el.remove(c)
    el.text = None
    el.attrib.clear()


def _move_content(src, dst):
    """Переносит определение из src в dst (тот должен быть пустой ссылкой)."""
    dst.attrib.clear()
    dst.attrib.update(src.attrib)
    dst.text = src.text
    for c in list(src):
        src.remove(c)
        dst.append(c)
    src.text = None


def repair_refs(root, groups):
    """
    После правки дерева восстанавливает инварианты XStream: определение — это первое вхождение
    в порядке документа, остальные — reference с пересчитанным относительным путём.
    Возвращает список предупреждений.
    """
    warns = []
    state = {}

    def refresh():
        state['pmap'] = parent_map(root)
        state['order'] = {el: i for i, el in enumerate(root.iter())}
    refresh()
    for target, refs in groups.items():
        order, pmap = state['order'], state['pmap']
        t_alive = target in order
        alive = [r for r in refs if r in order]
        members = alive + ([target] if t_alive else [])
        if not members:
            continue
        members.sort(key=order.get)
        same_tag = all(m.tag == target.tag for m in members)
        if not same_tag:
            if not t_alive:
                warns.append('Ссылки на удалённый элемент <%s> остались без определения' % target.tag)
                continue
            defn = target
        else:
            first = members[0]
            if first is not target:
                if t_alive:
                    tmp = ET.Element(target.tag)
                    _move_content(target, tmp)
                    _move_content(tmp, first)
                else:
                    _move_content(target, first)
                refresh()
                pmap = state['pmap']
            defn = first
        defn.attrib.pop('reference', None)
        changed = False
        for m in members:
            if m is defn:
                continue
            _become_reference(m)
            changed = True
        if changed:
            refresh()
            pmap = state['pmap']
        for m in members:
            if m is not defn:
                m.attrib['reference'] = make_ref_path(m, defn, pmap)
    return warns


# ---------------------------------------------------------------------------
# Распознавание элементов
# ---------------------------------------------------------------------------

def is_brick(el):
    t = el.get('type')
    if t is None or el.tag.endswith('Script'):
        return False
    return el.tag == 'brick' or el.tag.startswith(BRICK_PKG) or el.tag in C.SELF_ALIAS and el.tag.endswith('Brick')


def is_script(el):
    t = el.get('type')
    if t is None:
        return False
    return el.tag == 'script' or (el.tag.startswith(SCRIPT_PKG) and not el.tag.startswith(BRICK_PKG) and t.endswith('Script')) \
        or (el.tag in C.SELF_ALIAS and el.tag.endswith('Script'))


def is_object(el):
    return el.tag == 'object' and el.get('spriteId') is not None


def brick_tag(btype):
    if btype in C.FULLNAME_BRICKS:
        return BRICK_PKG + btype
    return btype if btype in C.SELF_ALIAS else 'brick'


def script_tag(stype):
    if stype in C.FULLNAME_SCRIPTS:
        return SCRIPT_PKG + stype
    return stype if stype in C.SELF_ALIAS else 'script'


def child(el, tag):
    for c in el:
        if c.tag == tag:
            return c
    return None


def child_text(el, tag, default=''):
    c = child(el, tag)
    return (c.text or '') if c is not None else default


def brick_title(btype):
    b = C.BLOCKS.get(btype)
    return b['title'] if b and b.get('title') else btype


def script_title(stype):
    for hb, sc in C.HEADER_BRICKS.items():
        if sc == stype:
            return brick_title(hb)
    return stype


# ---------------------------------------------------------------------------
# Формулы
# ---------------------------------------------------------------------------

class FNode:
    __slots__ = ('type', 'value', 'left', 'right', 'extra')

    def __init__(self, type_, value=None, left=None, right=None, extra=None):
        self.type, self.value, self.left, self.right, self.extra = type_, value, left, right, extra or []

    def children(self):
        return [c for c in ([self.left, self.right] + self.extra) if c is not None]

    def __repr__(self):
        return 'FNode(%s,%r)' % (self.type, self.value)


NODE_TYPES = ['NUMBER', 'STRING', 'OPERATOR', 'FUNCTION', 'SENSOR', 'USER_VARIABLE', 'USER_LIST',
              'USER_DEFINED_BRICK_INPUT', 'BRACKET', 'COLLISION_FORMULA']


def elem_to_node(e):
    if e is None:
        return None
    n = FNode(child_text(e, 'type'), child(e, 'value').text if child(e, 'value') is not None else None)
    if n.value is None and child(e, 'value') is not None:
        n.value = ''
    n.left = elem_to_node(child(e, 'leftChild'))
    n.right = elem_to_node(child(e, 'rightChild'))
    ac = child(e, 'additionalChildren')
    if ac is not None:
        n.extra = [elem_to_node(x) for x in ac]
    return n


def node_to_elem(n, tag, root=False):
    e = ET.Element(tag)
    if n.extra:
        ac = ET.SubElement(e, 'additionalChildren')
        for x in n.extra:
            ac.append(node_to_elem(x, FORMULA_ELEMENT))
    elif root:
        ET.SubElement(e, 'additionalChildren')
    if n.left is not None:
        e.append(node_to_elem(n.left, 'leftChild'))
    if n.right is not None:
        e.append(node_to_elem(n.right, 'rightChild'))
    ET.SubElement(e, 'type').text = n.type
    if n.value is not None:
        ET.SubElement(e, 'value').text = n.value
    return e


OP_SYMBOL = {'PLUS': '+', 'MINUS': '-', 'MULT': '*', 'DIVIDE': '/', 'MOD': 'mod', 'POW': '^', 'EQUAL': '=',
             'NOT_EQUAL': '!=', 'SMALLER_THAN': '<', 'GREATER_THAN': '>', 'SMALLER_OR_EQUAL': '<=',
             'GREATER_OR_EQUAL': '>=', 'LOGICAL_AND': 'and', 'LOGICAL_OR': 'or', 'LOGICAL_NOT': 'not',
             'STRING_CONCAT': '&'}
OP_PRIO = {'LOGICAL_OR': 1, 'LOGICAL_AND': 2, 'EQUAL': 3, 'NOT_EQUAL': 4, 'SMALLER_OR_EQUAL': 4, 'GREATER_OR_EQUAL': 4,
           'SMALLER_THAN': 4, 'GREATER_THAN': 4, 'LOGICAL_NOT': 4, 'PLUS': 5, 'MINUS': 5, 'STRING_CONCAT': 5,
           'MULT': 6, 'DIVIDE': 6, 'MOD': 6, 'POW': 7}
OP_ALIASES = {'+': 'PLUS', '-': 'MINUS', '*': 'MULT', '×': 'MULT', '/': 'DIVIDE', '÷': 'DIVIDE', 'mod': 'MOD',
              '%': 'MOD', '^': 'POW', '=': 'EQUAL', '==': 'EQUAL', '!=': 'NOT_EQUAL', '≠': 'NOT_EQUAL',
              '<>': 'NOT_EQUAL', '<': 'SMALLER_THAN', '>': 'GREATER_THAN', '<=': 'SMALLER_OR_EQUAL',
              '≤': 'SMALLER_OR_EQUAL', '>=': 'GREATER_OR_EQUAL', '≥': 'GREATER_OR_EQUAL', 'and': 'LOGICAL_AND',
              '&&': 'LOGICAL_AND', 'и': 'LOGICAL_AND', 'or': 'LOGICAL_OR', '||': 'LOGICAL_OR',
              'или': 'LOGICAL_OR', 'not': 'LOGICAL_NOT', '!': 'LOGICAL_NOT', 'не': 'LOGICAL_NOT', '&': 'STRING_CONCAT'}
_FUNC_SET = set(C.FUNCTIONS)
_SENS_SET = set(C.SENSORS)


def _q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def node_to_text(n, parent_prio=0):
    if n is None:
        return ''
    t, v = n.type, n.value or ''
    if t == 'NUMBER':
        return v
    if t == 'STRING':
        return _q(v)
    if t == 'USER_VARIABLE':
        return '[%s]' % v
    if t == 'USER_LIST':
        return '{%s}' % v
    if t == 'USER_DEFINED_BRICK_INPUT':
        return '@%s' % v
    if t == 'COLLISION_FORMULA':
        return '#%s' % v
    if t == 'SENSOR':
        return ('$' + v) if v in _FUNC_SET else v
    if t == 'BRACKET':
        inner = n.right if n.right is not None else (n.extra[-1] if n.extra else n.left)
        return '(%s)' % node_to_text(inner)
    if t == 'FUNCTION':
        args = [a for a in [n.left, n.right] + n.extra if a is not None]
        return '%s(%s)' % (v, '; '.join(node_to_text(a) for a in args))
    if t == 'OPERATOR':
        sym = OP_SYMBOL.get(v, v)
        pr = OP_PRIO.get(v, 0)
        if n.left is None:  # унарный
            s = sym + ('' if sym in ('-', '!') else ' ') + node_to_text(n.right, 7 if v == 'MINUS' else 5)
            return s if pr >= parent_prio or v == 'MINUS' and parent_prio <= 7 else '(%s)' % s
        s = '%s %s %s' % (node_to_text(n.left, pr), sym, node_to_text(n.right, pr + 1))
        return s if pr >= parent_prio else '(%s)' % s
    return '?%s' % t


class FormulaSyntaxError(ValueError):
    pass


_TOKEN = re.compile(r'''
    (?P<ws>\s+)
  | (?P<num>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|\.\d+)
  | (?P<str>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
  | (?P<var>\[[^\]]*\])
  | (?P<lst>\{[^}]*\})
  | (?P<inp>@[^\s()+\-*/^;,=<>!&|]+)
  | (?P<col>\#[^\s()+\-*/^;,=<>!&|]+)
  | (?P<id>\$?[^\W\d]\w*)
  | (?P<op><=|>=|==|!=|<>|&&|\|\||[+\-*/^=<>!&%×÷≠≤≥])
  | (?P<lp>\()
  | (?P<rp>\))
  | (?P<sep>[;,])
''', re.X | re.U)


def _tokenize(src):
    pos, out = 0, []
    while pos < len(src):
        m = _TOKEN.match(src, pos)
        if not m:
            raise FormulaSyntaxError('Неожиданный символ %r в позиции %d' % (src[pos], pos))
        pos = m.end()
        k = m.lastgroup
        if k != 'ws':
            out.append((k, m.group(), m.start()))
    out.append(('end', '', len(src)))
    return out


def _unq(s):
    q = s[0]
    body = s[1:-1]
    return re.sub(r'\\(.)', lambda m: '\n' if m.group(1) == 'n' else m.group(1), body)


class _Parser:
    def __init__(self, src):
        self.t = _tokenize(src)
        self.i = 0

    def peek(self):
        return self.t[self.i]

    def take(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def binop(self, tok):
        k, v, _ = tok
        if k == 'op':
            op = OP_ALIASES.get(v)
        elif k == 'id':
            op = OP_ALIASES.get(v.lower()) if v.lower() in ('and', 'or', 'mod', 'и', 'или') else None
        else:
            return None
        return op if op and op != 'LOGICAL_NOT' else None

    def parse(self):
        n = self.expr(1)
        if self.peek()[0] != 'end':
            raise FormulaSyntaxError('Лишний текст в позиции %d: %r' % (self.peek()[2], self.peek()[1]))
        return n

    def expr(self, minp):
        left = self.unary()
        while True:
            op = self.binop(self.peek())
            if op is None or OP_PRIO[op] < minp:
                break
            self.take()
            right = self.expr(OP_PRIO[op] + 1)
            left = FNode('OPERATOR', op, left, right)
        return left

    def unary(self):
        k, v, p = self.peek()
        if (k == 'op' and v in ('-', '!')) or (k == 'id' and v.lower() in ('not', 'не')):
            self.take()
            if v == '-':
                return FNode('OPERATOR', 'MINUS', None, self.unary_pow())
            return FNode('OPERATOR', 'LOGICAL_NOT', None, self.expr(5))
        return self.primary()

    def unary_pow(self):
        n = self.primary()
        while self.binop(self.peek()) == 'POW':
            self.take()
            n = FNode('OPERATOR', 'POW', n, self.unary())
        return n

    def primary(self):
        k, v, p = self.take()
        if k == 'num':
            return FNode('NUMBER', v)
        if k == 'str':
            return FNode('STRING', _unq(v))
        if k == 'var':
            return FNode('USER_VARIABLE', v[1:-1])
        if k == 'lst':
            return FNode('USER_LIST', v[1:-1])
        if k == 'inp':
            return FNode('USER_DEFINED_BRICK_INPUT', v[1:])
        if k == 'col':
            return FNode('COLLISION_FORMULA', v[1:])
        if k == 'lp':
            inner = self.expr(1)
            if self.take()[0] != 'rp':
                raise FormulaSyntaxError('Не закрыта скобка')
            return FNode('BRACKET', None, None, inner)
        if k == 'id':
            if v.startswith('$'):
                return FNode('SENSOR', v[1:])
            if self.peek()[0] == 'lp':
                self.take()
                args = []
                if self.peek()[0] != 'rp':
                    while True:
                        args.append(self.expr(1))
                        nk = self.take()
                        if nk[0] == 'rp':
                            break
                        if nk[0] != 'sep':
                            raise FormulaSyntaxError('Ожидалась «;» или «)» в позиции %d' % nk[2])
                else:
                    self.take()
                n = FNode('FUNCTION', v)
                if args:
                    n.left = args[0]
                if len(args) > 1:
                    n.right = args[1]
                n.extra = args[2:]
                return n
            if v in _SENS_SET:
                return FNode('SENSOR', v)
            if v in _FUNC_SET:
                return FNode('FUNCTION', v)
            if v.lower() in ('true', 'false'):
                return FNode('FUNCTION', v.upper())
            raise FormulaSyntaxError('Неизвестное имя «%s». Переменные пишутся в [скобках], списки в {скобках}, '
                                     'функции с аргументами — NAME(a; b)' % v)
        raise FormulaSyntaxError('Неожиданный элемент %r в позиции %d' % (v or 'конец', p))


def parse_formula_text(src):
    src = src.strip()
    if not src:
        return FNode('STRING', '')
    return _Parser(src).parse()


def formula_text(formula_el):
    return node_to_text(elem_to_node(formula_el))


def default_formula_node(category):
    return FNode('STRING', '') if category in STRING_FIELDS else FNode('NUMBER', '0')


def make_formula(category, node=None, key='category'):
    node = node or default_formula_node(category)
    e = node_to_elem(node, 'formula', root=True)
    e.set(key, category)
    # атрибут идёт первым, как в XStream
    return e


def formula_container(el):
    for tag in ('formulaList', 'formulaMap'):
        c = child(el, tag)
        if c is not None:
            return c
    return None


def get_formulas(el):
    fc = formula_container(el)
    return [f for f in fc if f.tag == 'formula'] if fc is not None else []


def formula_key(f):
    return f.get('category') or f.get('input') or '?'


def set_formula(el, category, node, key='category'):
    fc = formula_container(el)
    if fc is None:
        fc = ET.Element('formulaList')
        pos = 0
        for i, c in enumerate(el):
            if c.tag in ('brickId', 'commentedOut'):
                pos = i + 1
        el.insert(pos, fc)
    new = make_formula(category, node, key)
    for i, f in enumerate(list(fc)):
        if f.get(key) == category:
            fc.remove(f)
            fc.insert(i, new)
            return new
    fc.append(new)
    return new


# ---------------------------------------------------------------------------
# Шаблоны
# ---------------------------------------------------------------------------

def _leaf(parent, tag, text):
    e = ET.SubElement(parent, tag)
    e.text = text
    return e


def make_scene(name='Сцена'):
    s = ET.Element('scene', {'sceneId': new_uuid()})
    _leaf(s, 'name', name)
    ET.SubElement(s, 'objectList')
    return s


def make_object(name='Объект', otype='Sprite'):
    o = ET.Element('object', {'type': otype, 'spriteId': new_uuid(), 'name': name})
    for t in ('lookList', 'soundList', 'scriptList', 'nfcTagList', 'userVariables', 'userLists', 'userDefinedBrickList'):
        ET.SubElement(o, t)
    return o


def make_script(stype='StartScript'):
    s = ET.Element(script_tag(stype), {'type': stype, 'posX': '0.0', 'posY': '0.0'})
    ET.SubElement(s, 'brickList')
    _leaf(s, 'commentedOut', 'false')
    _leaf(s, 'scriptId', new_uuid())
    if stype == 'WhenConditionScript':
        fm = ET.SubElement(s, 'formulaMap')
        fm.append(make_formula('IF_CONDITION', FNode('NUMBER', '1')))
    extras = list(C.SCRIPT_FIELDS.get(stype, []))
    if stype == 'UserDefinedScript':
        extras.append(('userDefinedBrickID', new_uuid()))
    for name, val in sorted(extras):
        _leaf(s, name, val)
    if stype == 'UserDefinedScript':
        ET.SubElement(s, 'userDefinedBrickInputs')
    return s


def make_look(name, filename):
    l = ET.Element('look', {'fileName': filename, 'lookId': new_uuid(), 'name': name})
    _leaf(l, 'isWebRequest', 'false')
    _leaf(l, 'valid', 'true')
    return l


def make_sound(name, filename):
    s = ET.Element('sound', {'fileName': filename, 'name': name, 'soundId': new_uuid()})
    _leaf(s, 'midiFile', 'false')
    return s


def make_variable(name):
    v = ET.Element('userVariable', {'type': 'UserVariable', 'serialization': 'custom'})
    inner = ET.SubElement(v, 'userVariable')
    d = ET.SubElement(inner, 'default')
    _leaf(d, 'initialIndex', '-1')
    _leaf(d, 'deviceValueKey', new_uuid())
    _leaf(d, 'name', name)
    return v


def make_list(name):
    l = ET.Element('userList')
    _leaf(l, 'deviceListKey', new_uuid())
    _leaf(l, 'initialIndex', '-1')
    _leaf(l, 'name', name)
    return l


def make_brick(btype):
    b = ET.Element(brick_tag(btype), {'type': btype})
    _leaf(b, 'brickId', new_uuid())
    _leaf(b, 'commentedOut', 'false')
    fields = C.BRICK_FIELDS.get(btype)
    if fields:
        fl = ET.SubElement(b, 'formulaList')
        for cat in fields:
            fl.append(make_formula(cat))
    own = []
    for fname in C.COMPOSITE.get(btype, []):
        if fname != 'elseIfBranches':
            own.append((fname, None))
    for typ, fname, default in C.SIMPLE_FIELDS.get(btype, []):
        d = default.strip()
        if d.startswith('"') and d.endswith('"'):
            d = d[1:-1]
        elif d in SYMBOLIC_DEFAULTS:
            d = SYMBOLIC_DEFAULTS[d]
        elif d.startswith('PhysicsObject.Type.'):
            d = d.rsplit('.', 1)[1]
        elif d == '' and typ == 'String':
            d = ''
        elif d == '' or not re.match(r'^-?\d+(\.\d+)?$|^true$|^false$', d):
            continue
        own.append((fname, d))
    if btype == 'UserDefinedBrick':
        own += [('isCallingBrick', 'false'), ('userDefinedBrickDataList', None), ('userDefinedBrickID', new_uuid())]
    for fname, val in sorted(own):
        e = ET.SubElement(b, fname)
        if val is not None:
            e.text = val
    return b


def refresh_ids(el):
    """Новые UUID для скопированного поддерева (определения; ссылки не трогаем)."""
    for e in el.iter():
        if 'reference' in e.attrib:
            continue
        for a in ID_ATTRS:
            if a in e.attrib:
                e.set(a, new_uuid())
        if e.tag in ID_TAGS or e.tag in ('deviceValueKey', 'deviceListKey'):
            e.text = new_uuid()


# ---------------------------------------------------------------------------
# Проект
# ---------------------------------------------------------------------------

class Project:
    def __init__(self):
        self.path = None
        self.root = None
        self.files = {}       # имя записи архива -> bytes (всё кроме code.xml)
        self.is_zip = True
        self.undo_stack, self.redo_stack = [], []
        self.dirty = False
        self.warnings = []

    # --- создание/загрузка/сохранение
    @classmethod
    def new(cls, name='Новый проект', scene='Сцена', width=1080, height=1920):
        p = cls()
        hdr = {
            'applicationBuildName': '', 'applicationBuildNumber': '0', 'applicationBuildType': '',
            'applicationName': 'NewCatroid', 'applicationVersion': '2.2.0', 'catrobatLanguageVersion': '1.18',
            'customResolution': 'false', 'dateTimeUpload': '', 'description': '', 'deviceName': '',
            'isCastProject': 'false', 'landscapeMode': 'false', 'listeningLanguageTag': '', 'mediaLicense': '',
            'notesAndCredits': '', 'physicsHeightArea': '2.0', 'physicsWidthArea': '3.0', 'platform': 'Android',
            'platformVersion': '', 'programLicense': '', 'programName': name, 'remixOf': '', 'screenHeight': str(height),
            'screenMode': 'STRETCH', 'screenWidth': str(width), 'scenesEnabled': 'true', 'tags': '', 'url': '',
            'userHandle': '', 'gitRemoteUrl': '',
        }
        root = ET.Element('program')
        h = ET.SubElement(root, 'header')
        for k in sorted(hdr):
            _leaf(h, k, hdr[k])
        ET.SubElement(root, 'settings')
        sc = ET.SubElement(root, 'scenes')
        s = make_scene(scene)
        s.find('objectList').append(make_object('Фон'))
        sc.append(s)
        for t in ('programVariableList', 'programListOfLists', 'programMultiplayerVariableList'):
            ET.SubElement(root, t)
        _leaf(root, 'disableScientificNotation', 'false')
        p.root = root
        p.ensure_structure()
        p.dirty = True
        return p

    @classmethod
    def open(cls, path):
        p = cls()
        p.path = path
        with open(path, 'rb') as f:
            head = f.read(4)
        if head[:2] == b'PK':
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
                if 'code.xml' not in names:
                    raise ValueError('В архиве нет code.xml')
                p.root = parse_xml(z.read('code.xml'))
                for n in names:
                    if n != 'code.xml' and not n.endswith('/'):
                        p.files[n] = z.read(n)
            p.is_zip = True
        else:
            with open(path, 'rb') as f:
                p.root = parse_xml(f.read())
            p.is_zip = False
        if p.root.tag != 'program':
            raise ValueError('Корневой элемент не <program>: %s' % p.root.tag)
        return p

    def ensure_structure(self):
        """Каталоги сцен: <сцена>/images/.nomedia и <сцена>/sounds/.nomedia (как в архивах NewCatroid)."""
        added = []
        for sc in self.scenes():
            d = self.scene_dir(sc)
            for sub in ('images', 'sounds'):
                k = '%s/%s/.nomedia' % (d, sub)
                if k not in self.files:
                    self.files[k] = b''
                    added.append(k)
        return added

    def rename_scene(self, scene_el, new_name):
        """Переименовывает сцену и переносит её каталог в архиве."""
        old = self.scene_dir(scene_el)
        child(scene_el, 'name').text = new_name
        new = self.scene_dir(scene_el)
        if old != new:
            for k in list(self.files):
                if k.startswith(old + '/'):
                    self.files[new + k[len(old):]] = self.files.pop(k)

    def to_xml_bytes(self):
        return serialize_xml(self.root)

    def save(self, path=None, backup=True):
        path = path or self.path
        if not path:
            raise ValueError('Не указан путь')
        if self.is_zip:
            self.ensure_structure()
        data = self.to_xml_bytes()
        if backup and os.path.exists(path):
            shutil.copy2(path, path + '.bak')
        if self.is_zip:
            tmp = path + '.tmp'
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('code.xml', data)
                for n, b in self.files.items():
                    z.writestr(n, b)
            os.replace(tmp, path)
        else:
            with open(path, 'wb') as f:
                f.write(data)
        self.path = path
        self.dirty = False

    def export_code_xml(self, path):
        with open(path, 'wb') as f:
            f.write(self.to_xml_bytes())

    # --- правки с отменой и починкой ссылок
    @contextlib.contextmanager
    def edit(self):
        snap = self.to_xml_bytes()
        groups = collect_groups(self.root)
        try:
            yield groups
        except Exception:
            self.root = parse_xml(snap)
            raise
        self.warnings = repair_refs(self.root, groups)
        self.undo_stack.append(snap)
        if len(self.undo_stack) > 60:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self.dirty = True

    def undo(self):
        if not self.undo_stack:
            return False
        self.redo_stack.append(self.to_xml_bytes())
        self.root = parse_xml(self.undo_stack.pop())
        self.dirty = True
        return True

    def redo(self):
        if not self.redo_stack:
            return False
        self.undo_stack.append(self.to_xml_bytes())
        self.root = parse_xml(self.redo_stack.pop())
        self.dirty = True
        return True

    # --- навигация
    def scenes(self):
        sc = child(self.root, 'scenes')
        return [s for s in sc] if sc is not None else []

    def scene_of(self, el, pmap=None):
        pmap = pmap or parent_map(self.root)
        while el is not None:
            if el.tag == 'scene':
                return el
            el = pmap.get(el)
        return None

    def object_of(self, el, pmap=None):
        pmap = pmap or parent_map(self.root)
        while el is not None:
            if is_object(el):
                return el
            el = pmap.get(el)
        return None

    def path_of(self, el):
        """Путь из индексов детей от корня (для восстановления выбора после undo)."""
        pmap = parent_map(self.root)
        out = []
        while el in pmap:
            p = pmap[el]
            out.append(list(p).index(el))
            el = p
        return out[::-1]

    def by_path(self, idxs):
        el = self.root
        for i in idxs:
            if i >= len(el):
                break
            el = el[i]
        return el

    # --- копирование с учётом ссылок
    def clone(self, el):
        """
        Глубокая копия поддерева для вставки. Ссылки внутри поддерева указывают на копии, ссылки
        наружу остаются; определения, на которые ссылаются снаружи, в копии становятся ссылками
        на оригинал. Возвращает (копия, [(элемент-ссылка в копии, цель)]).
        """
        pmap = parent_map(self.root)
        groups = collect_groups(self.root)
        inside = set(el.iter())
        mapping = {}

        def dup(o):
            c = ET.Element(o.tag, dict(o.attrib))
            c.text = o.text
            mapping[o] = c
            for ch in o:
                c.append(dup(ch))
            return c
        c = dup(el)
        converted = {o for o in mapping if o.get('reference') is None and o in groups
                     and any(r not in inside for r in groups[o])}
        links = []
        for o, cp in mapping.items():
            ref = o.get('reference')
            if ref is not None:
                t = resolve_ref(o, pmap, ref, self.root)
                if t is not None:
                    links.append((cp, t if t in converted else mapping.get(t, t)))
            elif o in converted:
                _become_reference(cp)
                cp.attrib['reference'] = '.'
                links.append((cp, o))
        refresh_ids(c)
        return c, links

    def insert_clone(self, parent, index, el):
        """Вставка копии поддерева одним действием (с отменой). Возвращает вставленную копию."""
        c, links = self.clone(el)
        with self.edit() as g:
            parent.insert(index, c)
            for cp, t in links:
                g.setdefault(t, []).append(cp)
        return c

    # --- словари
    def variables(self):
        """Определения переменных: [(имя, элемент-определение, область)]."""
        out = []
        pmap = parent_map(self.root)
        groups = collect_groups(self.root)
        global_defs = set()
        gl = child(self.root, 'programVariableList')
        if gl is not None:
            for v in gl:
                t = resolve_ref(v, pmap, v.get('reference'), self.root) if v.get('reference') else v
                if t is not None:
                    global_defs.add(t)
        for el in self.root.iter('userVariable'):
            if el.get('reference') is not None or el.get('type') != 'UserVariable':
                continue
            par = pmap.get(el)
            if par is not None and par.tag == 'userDefinedBrickInputs':
                continue
            nm = el.find('.//name')
            if nm is None:
                continue
            scope = 'глобальная' if el in global_defs else 'локальная'
            out.append((nm.text or '', el, scope))
        return out

    def lists(self):
        out = []
        pmap = parent_map(self.root)
        global_defs = set()
        gl = child(self.root, 'programListOfLists')
        if gl is not None:
            for v in gl:
                t = resolve_ref(v, pmap, v.get('reference'), self.root) if v.get('reference') else v
                if t is not None:
                    global_defs.add(t)
        for el in self.root.iter('userList'):
            if el.get('reference') is not None:
                continue
            nm = el.find('name')
            if nm is None:
                continue
            out.append((nm.text or '', el, 'глобальный' if el in global_defs else 'локальный'))
        return out

    def ref_target(self, el):
        ref = el.get('reference')
        if ref is None:
            return el
        return resolve_ref(el, parent_map(self.root), ref, self.root)

    # --- файлы архива
    def scene_dir(self, scene_el):
        return encode_dir_name(child_text(scene_el, 'name'))

    def add_file(self, arcname, data):
        self.files[arcname] = data
        self.dirty = True

    def add_image(self, scene_el, srcpath):
        base = os.path.basename(srcpath)
        d = self.scene_dir(scene_el)
        name, n = base, 0
        stem, ext = os.path.splitext(base)
        while '%s/images/%s' % (d, name) in self.files:
            name = '%s_#%d%s' % (stem, n, ext)
            n += 1
        with open(srcpath, 'rb') as f:
            self.files['%s/images/%s' % (d, name)] = f.read()
        self.files.setdefault('%s/images/.nomedia' % d, b'')
        return name

    def add_sound(self, scene_el, srcpath):
        base = os.path.basename(srcpath)
        d = self.scene_dir(scene_el)
        name, n = base, 0
        stem, ext = os.path.splitext(base)
        while '%s/sounds/%s' % (d, name) in self.files:
            name = '%s_#%d%s' % (stem, n, ext)
            n += 1
        with open(srcpath, 'rb') as f:
            self.files['%s/sounds/%s' % (d, name)] = f.read()
        self.files.setdefault('%s/sounds/.nomedia' % d, b'')
        return name


# ---------------------------------------------------------------------------
# Проверка
# ---------------------------------------------------------------------------

def validate(proj):
    """Возвращает список (уровень, элемент, сообщение). Уровни: ОШИБКА, ПРЕДУПРЕЖДЕНИЕ, ИНФО."""
    res = []
    root = proj.root
    pmap = parent_map(root)

    def add(level, el, msg):
        res.append((level, el, msg))
    if root.tag != 'program':
        add('ОШИБКА', root, 'Корневой элемент должен быть <program>')
    hdr = child(root, 'header')
    if hdr is None:
        add('ОШИБКА', root, 'Нет <header>')
    else:
        try:
            v = float(child_text(hdr, 'catrobatLanguageVersion', '0') or 0)
            if v > CURRENT_LANGUAGE_VERSION:
                add('ОШИБКА', hdr, 'Версия языка %s новее 1.18: приложение не загрузит проект' % v)
            elif v < 0.9 and v != 0.8:
                add('ОШИБКА', hdr, 'Версия языка %s не поддерживается' % v)
            elif v < CURRENT_LANGUAGE_VERSION:
                add('ИНФО', hdr, 'Версия языка %s < 1.18: приложение выполнит миграцию при загрузке' % v)
        except ValueError:
            add('ОШИБКА', hdr, 'catrobatLanguageVersion не число')
    expected = ['header', 'settings', 'scenes', 'programVariableList', 'programListOfLists',
                'programMultiplayerVariableList', 'disableScientificNotation']
    tags = [c.tag for c in root]
    if tags != expected:
        add('ПРЕДУПРЕЖДЕНИЕ', root, 'Порядок/состав тегов <program> отличается от стандартного: %s' % ', '.join(tags))
    scenes = proj.scenes()
    if not scenes:
        add('ОШИБКА', root, 'В проекте нет ни одной сцены')
    seen_ids = {}
    scene_names = set()
    for sc in scenes:
        nm = child_text(sc, 'name')
        if not sc.get('sceneId'):
            add('ОШИБКА', sc, 'У сцены нет sceneId')
        if nm in scene_names:
            add('ОШИБКА', sc, 'Повторяющееся имя сцены «%s»' % nm)
        scene_names.add(nm)
        obj_names = set()
        ol = child(sc, 'objectList')
        for ob in (ol if ol is not None else []):
            if ob.get('type', 'Sprite') not in OBJECT_TYPES:
                add('ПРЕДУПРЕЖДЕНИЕ', ob, 'Неизвестный тип объекта %s' % ob.get('type'))
            if not ob.get('spriteId') or ob.get('name') is None:
                add('ОШИБКА', ob, 'У объекта должны быть атрибуты spriteId и name')
            if ob.get('name') in obj_names:
                add('ОШИБКА', ob, 'Повторяющееся имя объекта «%s» в сцене «%s»' % (ob.get('name'), nm))
            obj_names.add(ob.get('name'))
            for lk in ob.iterfind('lookList/look'):
                if lk.get('reference') is not None:
                    continue
                fn = lk.get('fileName')
                if proj.files or proj.is_zip and proj.path:
                    key = '%s/images/%s' % (proj.scene_dir(sc), fn)
                    if key not in proj.files:
                        add('ПРЕДУПРЕЖДЕНИЕ', lk, 'Файл образа не найден в архиве: %s' % key)
            for sn in ob.iterfind('soundList/sound'):
                if sn.get('reference') is not None:
                    continue
                fn = sn.get('fileName')
                if proj.files or proj.is_zip and proj.path:
                    key = '%s/sounds/%s' % (proj.scene_dir(sc), fn)
                    if key not in proj.files:
                        add('ПРЕДУПРЕЖДЕНИЕ', sn, 'Файл звука не найден в архиве: %s' % key)
    # ссылки
    order = {el: i for i, el in enumerate(root.iter())}
    for el in root.iter():
        ref = el.get('reference')
        if ref is None:
            continue
        t = resolve_ref(el, pmap, ref, root)
        if t is None:
            add('ОШИБКА', el, 'Ссылка reference="%s" ни на что не указывает' % ref)
        elif order[t] > order[el]:
            add('ОШИБКА', el, 'Ссылка указывает на элемент, который идёт в документе позже (XStream так не прочитает)')
    # идентификаторы
    for el in root.iter():
        for a in ID_ATTRS:
            if el.get(a) is not None and el.get('reference') is None:
                seen_ids.setdefault(el.get(a), []).append(el)
        if el.tag in ID_TAGS and el.text:
            seen_ids.setdefault(el.text, []).append(el)
    for k, v in seen_ids.items():
        if len(v) > 1:
            add('ОШИБКА', v[1], 'Повторяющийся идентификатор %s (%d раза)' % (k, len(v)))
    # скрипты и блоки
    def check_formula_tree(f, node_el, where):
        if node_el is None:
            return
        t = child_text(node_el, 'type')
        v = child_text(node_el, 'value')
        if t not in NODE_TYPES:
            add('ОШИБКА', f, '%s: неизвестный тип узла формулы «%s»' % (where, t))
        elif t == 'OPERATOR' and v not in C.OPERATORS:
            add('ОШИБКА', f, '%s: неизвестный оператор «%s»' % (where, v))
        elif t == 'FUNCTION' and v not in _FUNC_SET:
            add('ИНФО', f, '%s: функции «%s» нет в Functions — вероятно, пользовательская формула из .newlib' % (where, v))
        elif t == 'SENSOR' and v not in _SENS_SET:
            add('ИНФО', f, '%s: датчик «%s» отсутствует в каталоге (каталог неполный)' % (where, v))
        for tag in ('leftChild', 'rightChild'):
            check_formula_tree(f, child(node_el, tag), where)
        ac = child(node_el, 'additionalChildren')
        for x in (ac if ac is not None else []):
            check_formula_tree(f, x, where)

    def check_formulas(owner, label):
        for f in get_formulas(owner):
            cat = f.get('category')
            if cat is not None and cat not in C.BRICKFIELDS:
                add('ОШИБКА', f, '%s: category="%s" нет в BrickField — приложение выбросит исключение при загрузке' % (label, cat))
            check_formula_tree(f, f, label)

    def check_brick(b):
        bt = b.get('type')
        label = brick_title(bt)
        if bt not in C.BLOCKS and bt not in C.BRICK_FIELDS and not bt.endswith('Brick'):
            add('ПРЕДУПРЕЖДЕНИЕ', b, 'Неизвестный тип блока «%s»' % bt)
        elif bt not in C.BLOCKS and bt not in C.BRICK_FIELDS:
            add('ИНФО', b, 'Тип блока «%s» отсутствует в каталоге' % bt)
        if child(b, 'brickId') is None:
            add('ПРЕДУПРЕЖДЕНИЕ', b, '%s: нет brickId' % label)
        if b.tag != 'brick' and not b.tag.startswith(BRICK_PKG) and b.tag != bt:
            add('ПРЕДУПРЕЖДЕНИЕ', b, '%s: имя элемента <%s> не соответствует type' % (label, b.tag))
        if b.tag == 'brick' and bt in C.FULLNAME_BRICKS:
            add('ОШИБКА', b, '%s: у этого класса нет алиаса, элемент должен называться %s%s' % (label, BRICK_PKG, bt))
        allowed = C.BRICK_FIELDS.get(bt)
        for f in get_formulas(b):
            cat = f.get('category')
            if cat is not None and allowed is not None and cat not in allowed and bt not in ('CustomBrick', 'UserDefinedBrick'):
                add('ПРЕДУПРЕЖДЕНИЕ', f, '%s: category="%s" не входит в допустимые поля блока (%s)' % (label, cat, ', '.join(allowed)))
        check_formulas(b, label)
        for fld in C.COMPOSITE.get(bt, []):
            lst = child(b, fld)
            if lst is not None:
                for sub in lst:
                    if is_brick(sub):
                        check_brick(sub)
                    elif sub.tag != 'org.catrobat.catroid.content.bricks.IfLogicBeginBrick$ElseIfBranch':
                        pass

    for sc in scenes:
        for ob in sc.iterfind('objectList/object'):
            for scr in ob.iterfind('scriptList/*'):
                if not is_script(scr):
                    add('ПРЕДУПРЕЖДЕНИЕ', scr, 'Неопознанный элемент в scriptList: <%s>' % scr.tag)
                    continue
                st = scr.get('type')
                if st not in C.SCRIPTS and st != 'Script':
                    add('ПРЕДУПРЕЖДЕНИЕ', scr, 'Неизвестный тип скрипта «%s»' % st)
                if st in C.FULLNAME_SCRIPTS and scr.tag == 'script':
                    add('ОШИБКА', scr, 'У %s нет алиаса: элемент должен называться %s%s' % (st, SCRIPT_PKG, st))
                if child(scr, 'scriptId') is None:
                    add('ПРЕДУПРЕЖДЕНИЕ', scr, '%s: нет scriptId' % st)
                check_formulas(scr, script_title(st))
                bl = child(scr, 'brickList')
                for b in (bl if bl is not None else []):
                    if is_brick(b):
                        check_brick(b)
            for ub in ob.iterfind('userDefinedBrickList/*'):
                if is_brick(ub):
                    check_brick(ub)
    return res


def element_summary(el):
    """Краткое описание элемента для сообщений."""
    if is_object(el):
        return 'объект «%s»' % el.get('name')
    if el.tag == 'scene':
        return 'сцена «%s»' % child_text(el, 'name')
    if is_script(el):
        return 'скрипт %s' % script_title(el.get('type'))
    if is_brick(el):
        return 'блок %s' % brick_title(el.get('type'))
    return '<%s>' % el.tag


# ---------------------------------------------------------------------------
# Сервисные функции
# ---------------------------------------------------------------------------

def unused_files(proj):
    """Файлы образов и звуков в каталогах сцен, на которые не ссылается ни один look/sound."""
    used = set()
    for sc in proj.scenes():
        d = proj.scene_dir(sc)
        for lk in sc.iter('look'):
            if lk.get('fileName') and lk.get('reference') is None:
                used.add('%s/images/%s' % (d, lk.get('fileName')))
        for sn in sc.iter('sound'):
            if sn.get('fileName') and sn.get('reference') is None:
                used.add('%s/sounds/%s' % (d, sn.get('fileName')))
    out = []
    dirs = {proj.scene_dir(sc) for sc in proj.scenes()}
    for name in proj.files:
        parts = name.split('/')
        if len(parts) >= 2 and parts[0] not in dirs and parts[0] not in ('files', 'libs', 'libs_processed', 'jniLibs') \
                and parts[1] in ('images', 'sounds'):
            out.append(name)
            continue
        if len(parts) == 3 and parts[1] in ('images', 'sounds') and parts[2] != '.nomedia' and name not in used:
            out.append(name)
    return out


def search(root, text):
    """Поиск по атрибутам, тексту и формулам. Возвращает список (элемент, что найдено)."""
    t = text.lower()
    out = []
    for el in root.iter():
        for k, v in el.attrib.items():
            if t in (v or '').lower():
                out.append((el, '%s=%s' % (k, v)))
        if not len(el) and el.text and t in el.text.lower():
            out.append((el, '<%s>%s' % (el.tag, el.text[:80])))
        if el.tag == 'formula':
            ft = formula_text(el)
            if t in ft.lower():
                out.append((el, ft[:100]))
    return out


def rename_in_formulas(root, node_type, old, new):
    """Переименование переменной/списка в узлах формул (они ссылаются по имени)."""
    n = 0
    for e in root.iter():
        if e.tag in ('formula', 'leftChild', 'rightChild', FORMULA_ELEMENT):
            ty, va = child(e, 'type'), child(e, 'value')
            if ty is not None and va is not None and ty.text == node_type and va.text == old:
                va.text = new
                n += 1
    return n


def retarget_groups(groups, old, new):
    """После замены элемента old на new (разбор XML) переносит ссылки на новое поддерево."""
    def walk(a, b):
        if a in groups:
            groups[b] = groups.pop(a)
        if a.tag == b.tag and len(a) == len(b):
            for x, y in zip(a, b):
                walk(x, y)
    walk(old, new)


def object_names(scene_el):
    ol = child(scene_el, 'objectList')
    return {o.get('name') for o in (ol if ol is not None else [])}


def unique_name(base, taken):
    if base not in taken:
        return base
    n = 1
    while '%s (%d)' % (base, n) in taken:
        n += 1
    return '%s (%d)' % (base, n)
