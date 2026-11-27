# -*- coding: utf-8 -*-
"""Строит newtrobat_catalog.py из документации (blocks reference + format spec)."""
import re, sys, json, pprint

def read(p): return open(p, encoding='utf-8').read().split('\n')

def parse_blocks(path):
    L = read(path)
    cat = ''; cats = {}
    blocks = {}
    i = 0
    while i < len(L):
        l = L[i]
        m = re.match(r'^## (.+?) \(`(\w+)`\)', l)
        if m: cat = m.group(1); i += 1; continue
        if l.startswith('### ') and i + 2 < len(L) and 'Страница wiki' in L[i + 2]:
            title = l[4:].strip(); j = i + 1; b = {'title': title, 'cat': cat, 'fields': [], 'other': '', 'purpose': '', 'params': []}
            btype = None
            while j < len(L) and not L[j].startswith('### ') and not L[j].startswith('## ') and L[j].strip() != '---':
                x = L[j]
                m = re.match(r'^- Тип блока в XML.*?: `(\w+)`', x)
                if m: btype = m.group(1)
                m = re.match(r'^- Поля формул.*?: (.+)$', x)
                if m and 'нет' not in m.group(1)[:5]:
                    b['fields'] = re.findall(r'`?([A-Z][A-Z0-9_]+)`?', m.group(1).split('(')[0] if m.group(1).startswith('нет') else m.group(1))
                m = re.match(r'^- Прочие поля.*?: (.+)$', x)
                if m: b['other'] = m.group(1)
                if x.startswith('**Назначение.**'): b['purpose'] = x[len('**Назначение.**'):].strip()
                m = re.match(r'^\| `(.+?)` \| (.*?) \| (.*?) \| (.*) \|$', x)
                if m: b['params'].append([m.group(1), m.group(2), m.group(3).strip('`'), m.group(4)])
                j += 1
            if btype: blocks[btype] = b
            i = j; continue
        i += 1
    return blocks

def parse_spec(path):
    L = read(path); txt = '\n'.join(L)
    spec = {}
    # table brick -> fields (6.20)
    tbl = {}
    inb = False
    for l in L:
        if l.startswith('**Таблица по блокам**'): inb = True; continue
        if inb:
            if l.startswith('```') and tbl: break
            m = re.match(r'^(\w+Brick\w*): (.+)$', l)
            if m: tbl[m.group(1)] = [f.strip() for f in m.group(2).split(',') if f.strip()]
    spec['brick_fields'] = tbl
    # functions / sensors / operators
    def names_from(a, b):
        out = []
        for l in L[a - 1:b]:
            if l.startswith('|'):
                cells = l.split('|')
                if len(cells) > 2: out += re.findall(r'`([A-Z][A-Z0-9_/]+)`', cells[2])
            elif l.startswith('`'):
                out += re.findall(r'`([A-Z][A-Z0-9_/]+)`', l)
        return out
    def expand(names):
        res = []
        for n in names:
            m = re.match(r'^(.*?)([A-Z]+(?:/[A-Z]+)+)$', n)
            if '/' in n:
                head, tail = n.rsplit('_', 1) if '_' in n else ('', n)
                for t in tail.split('/'): res.append((head + '_' if head else '') + t)
            else: res.append(n)
        return res
    idx = {l[:12]: i for i, l in enumerate(L)}
    def sec(prefix):
        for i, l in enumerate(L):
            if l.startswith(prefix): return i + 1
    s_fun = sec('### 6.8.'); s_ops = sec('### 6.9.'); s_sen = sec('### 6.7.'); s_scr = sec('### 6.11.')
    funcs = expand(names_from(s_fun, s_ops - 1))
    spec['functions'] = sorted(set(f for f in funcs if f not in ('TEXT', 'LIST', 'BOOLEAN')))
    sens = []
    for l in L[s_sen - 1:s_fun - 1]:
        if l.startswith('`OBJECT_X'): sens += re.findall(r'`([A-Z][A-Z0-9_]+)`', l)
        elif l.startswith('|') and not l.startswith('|---') and 'Группа' not in l:
            cells = l.split('|')
            if len(cells) > 2 and 'Поза' not in cells[1]: sens += re.findall(r'`([A-Z][A-Z0-9_]+)`', cells[2])
    spec['sensors_raw'] = sens
    ops = []
    for l in L[s_ops - 1:s_ops + 25]:
        m = re.match(r'^\| `([A-Z_]+)` \| (\d+) \|', l)
        if m: ops.append(m.group(1))
    spec['operators'] = ops
    scripts = re.findall(r'`(\w+Script)`', L[s_scr + 1])
    spec['scripts'] = scripts
    # script header brick -> script
    hb = {}
    for l in L:
        m = re.match(r'^\| `(\w+Brick)` \| `(\w+)` \| `(\w+Script)` \|', l)
        if m: hb[m.group(1)] = m.group(3)
    spec['header_bricks'] = hb
    # composite fields
    comp = {}
    for l in L:
        m = re.match(r'^\| `(\w+Brick)` \| (`\w+`.*) \|$', l)
        if m and ('List<Brick>' in m.group(2) or 'ElseIfBranch' in m.group(2)):
            comp[m.group(1)] = re.findall(r'`(\w+)` \(`List<', m.group(2))
    spec['composite'] = comp
    comp['RaspiIfLogicBeginBrick'] = comp.get('IfLogicBeginBrick', [])
    # simple fields:  Block: int x = 0; ...
    simple = {}
    start = None
    for i, l in enumerate(L):
        if l.startswith('**Простые поля'): start = i
        if start and i > start and l.startswith('```'):
            j = i + 1
            while not L[j].startswith('```'):
                m = re.match(r'^(\w+Brick): (.+)$', L[j])
                if m:
                    flds = []
                    for part in m.group(2).split(';'):
                        mm = re.match(r'\s*([\w<>\.\[\]]+) (\w+)(?: = (.*))?$', part.strip())
                        if mm: flds.append((mm.group(1), mm.group(2), (mm.group(3) or '').strip()))
                    simple[m.group(1)] = flds
                j += 1
            break
    spec['simple_fields'] = simple
    # brickfield enum from 6.1
    bf = set()
    a = sec('### 6.1.'); b = sec('### 6.2.')
    for l in L[a - 1:b - 1]:
        bf.update(re.findall(r'`([A-Z][A-Z0-9_]+)`', l))
    for n in range(1, 18): bf.add('VALUE_%d' % n)
    for n in range(1, 8): bf.add('FORMULA_%d' % n)
    for n in range(1, 11): bf.add('CUSTOM_PARAM_%d' % n)
    spec['brickfields'] = sorted(bf)
    # справка по функциям (6.27)
    fh = {}
    a = sec('### 6.27.'); b = sec('### 6.28.')
    for l in L[a - 1:b - 1]:
        m = re.match(r'^\| ((?:`[A-Z0-9_/]+`,? ?)+) \| (.*?) \| (.*) \|$', l)
        if m:
            for nm in expand(re.findall(r'`([A-Z0-9_/]+)`', m.group(1))):
                fh[nm] = [m.group(2).strip()[:160], m.group(3).strip()[:300]]
    spec['func_help'] = fh
    return spec

if __name__ == '__main__':
    up = '/mnt/user-data/uploads/'
    blocks = parse_blocks(up + 'newtrobat_blocks_reference_2_2_0.md')
    spec = parse_spec(up + 'newtrobat_format_spec_2_2_0.md')
    print(len(blocks), len(spec['brick_fields']), len(spec['functions']), len(spec['sensors_raw']), spec['operators'], len(spec['scripts']), len(spec['header_bricks']), spec['composite'], len(spec['simple_fields']), len(spec['brickfields']))
    json.dump({'blocks': blocks, 'spec': spec}, open('raw.json', 'w'), ensure_ascii=False)


def emit(out='newtrobat_catalog.py', up='/mnt/user-data/uploads/'):
    blocks = parse_blocks(up + 'newtrobat_blocks_reference_2_2_0.md')
    spec = parse_spec(up + 'newtrobat_format_spec_2_2_0.md')
    bf = dict(spec['brick_fields'])
    slim = {}
    for t, b in blocks.items():
        slim[t] = {'title': b['title'], 'cat': b['cat'], 'purpose': b['purpose'][:700],
                   'params': [p[:4] for p in b['params']][:12]}
        if t not in bf and b['fields']: bf[t] = b['fields']
    for t in bf:
        slim.setdefault(t, {'title': t, 'cat': '', 'purpose': '', 'params': []})
    for t in spec['header_bricks']:
        slim.setdefault(t, {'title': t, 'cat': 'События', 'purpose': '', 'params': []})
    L = read(up + 'newtrobat_format_spec_2_2_0.md')
    uv = ul = []
    for l in L:
        if l.startswith('- `userVariable` (`UserVariable`) получают'): uv = re.findall(r'`(\w+Brick)`', l.split(':', 1)[1])
        if l.startswith('- `userList` (`UserList`) получают'): ul = re.findall(r'`(\w+Brick)`', l.split(':', 1)[1])
    uv += ['ChooseFileBrick', 'ReadVariableFromFileBrick', 'AskGPTBrick', 'WebRequestBrick', 'WriteVariableToFileBrick', 'StartListeningBrick']
    ul += ['ParameterizedEndBrick']
    consts = {
        'USERVAR_BRICKS': sorted(set(uv)),
        'USERLIST_BRICKS': sorted(set(ul)),
        'REF_FIELDS': {'look': ['SetLookBrick', 'SetBackgroundBrick', 'SetHitboxBrick'],
                       'sound': ['PlaySoundBrick', 'PlaySoundAtBrick', 'SetSoundVolumeBrick', 'StopSoundBrick']},
        'SCRIPT_FIELDS': {'BroadcastScript': [('receivedMessage', '')], 'RaspiInterruptScript': [('eventValue', ''), ('pin', '')],
                          'UserDefinedScript': [('screenRefresh', 'true')],
                          'WhenBounceOffScript': [('spriteToBounceOffName', '')], 'WhenGamepadButtonScript': [('action', '')],
                          'WhenMouseButtonClickedScript': [('buttonCode', '0')], 'WhenNfcScript': [('matchAll', 'true')]},
        'FUNCTIONS': spec['functions'],
        'SENSORS': sorted(set(spec['sensors_raw'])),
        'OPERATORS': spec['operators'],
        'SCRIPTS': spec['scripts'],
        'HEADER_BRICKS': spec['header_bricks'],
        'COMPOSITE': spec['composite'],
        'BRICK_FIELDS': bf,
        'SIMPLE_FIELDS': {k: [list(x) for x in v] for k, v in spec['simple_fields'].items()},
        'BRICKFIELDS': spec['brickfields'],
        'FULLNAME_BRICKS': ['ClearSceneBrick', 'CreateCubeBrick', 'CreateSpringConstraintBrick', 'PlayPreparedSoundBrick', 'PrepareSoundBrick', 'SavePlotBrick', 'SetObjectTextureBrick', 'SetSaveScenesBrick', 'SetStopSoundsBrick', 'ShowVarFontBrick', 'StartPlotBrick', 'StopPlotBrick', 'WhenAppMinimizedBrick', 'WhenAppRestoredBrick', 'WhenFingerMovedOnScreenBrick', 'WhenFingerMovedOverSpriteBrick', 'WhenNotificationActionTriggeredBrick', 'WhenSpriteReleasedBrick', 'WhenWindowResizedBrick'],
        'FULLNAME_SCRIPTS': ['AfterUpdateScript', 'BackPressedScript', 'BeforeUpdateScript', 'ExitProjectScript', 'WhenMouseButtonClickedScript', 'WhenMouseWheelScrolledScript'],
        'FUNC_HELP': spec['func_help'],
        'SELF_ALIAS': ['Fast2DSetGravityBrick', 'WhenClonedWithNameBrick', 'WhenClonedWithNameScript', 'CustomBrick', 'RunAsSpriteBrick'],
    }
    with open(out, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n"""Каталог блоков/функций/датчиков NewCatroid 2.2.0.\nСгенерировано build_catalog.py из newtrobat_format_spec_2_2_0.md и newtrobat_blocks_reference_2_2_0.md.\n"""\n\n')
        f.write('BLOCKS = ')
        pprint.pprint(slim, stream=f, width=140, compact=True)
        for k, v in consts.items():
            f.write('\n%s = ' % k)
            pprint.pprint(v, stream=f, width=140, compact=True)
    print('written', out, len(slim), 'blocks')

if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'emit':
    emit()
