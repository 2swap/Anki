"""Build Go life-and-death notes from Sensei's Library diagrams (sldata.json).

A note is defined by a base diagram and a list of lines. Each line is a list of
moves read from numbered diagrams, so coordinates are never typed by hand.
Every line is replayed with capture and ko rules before it becomes a card.
"""
import json, os, re, sys

DATA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data', 'sldata.json')))
N = 19


def _flip(d):
    """Orientation that puts the diagram's board edges at the top/left."""
    e = d['edges']
    return ('B' in e and 'T' not in e), ('R' in e and 'L' not in e)


def cells(page, n):
    """{(x, y): label} in absolute coordinates, flipped so edges are top/left."""
    d = DATA[page]['diagrams'][str(n)]
    fy, fx = _flip(d)
    out = {}
    for j, row in enumerate(d['grid']):
        for i, lab in enumerate(row):
            x, y = d['off'][0] + i, d['off'][1] + j
            if fx: x = N - 1 - x
            if fy: y = N - 1 - y
            out[(x, y)] = lab
    return out


def base(page, n):
    """Stones of a diagram, without its numbered moves: {(x, y): 'X'|'O'}."""
    return {p: lab[0] for p, lab in cells(page, n).items() if lab[:1] in ('X', 'O')}


def numbered(page, n):
    """{move number: (colour, point)} for the numbered stones of a diagram."""
    out = {}
    for p, lab in cells(page, n).items():
        m = re.fullmatch(r'([BW])(\d+)', lab)
        if m:
            out[int(m.group(2))] = ('X' if m.group(1) == 'B' else 'O', p)
    return out


def letter(page, n, a):
    pts = [p for p, lab in cells(page, n).items() if lab == a]
    assert len(pts) == 1, (page, n, a, pts)
    return pts[0]


def seq(page, n, at=None, upto=None, first=1, last=None):
    """Moves of a numbered diagram in order. `at` places moves that sit on an
    earlier stone ({8: 'W5'} = 8 at 5; {4: 'a'} = at letter a). A missing
    number is a tenuki (pass). Returns [(colour, point or None)]."""
    at = at or {}
    nums = numbered(page, n)
    hi = max(list(nums) + list(at)) if (nums or at) else 0
    if upto: hi = upto
    out = []
    for k in range(first, hi + 1):
        if k in at:
            ref = at[k]
            col = None
            if isinstance(ref, tuple):
                col, p = ref
            elif re.fullmatch(r'[BW]\d+', ref):
                p = nums[int(ref[1:])][1]
            else:
                p = letter(page, n, ref)
            if col is None:
                # colour alternates with the previous move of known colour
                col = _colour_of(k, nums, first)
            out.append((col, p))
        elif k in nums:
            out.append(nums[k])
        else:
            out.append((_colour_of(k, nums, first), None))
    return _tag(out, page, n, first)


def _colour_of(k, nums, first):
    j, (c, p) = next(iter(nums.items()))
    return c if (j - k) % 2 == 0 else ('O' if c == 'X' else 'X')


def lt(page, n, *specs):
    """Moves at lettered points: lt(page, n, 'Wa', 'Bb') = White a, Black b."""
    return _tag([('X' if s[0] == 'B' else 'O', letter(page, n, s[1:])) for s in specs], page, n, 10 ** 9)


def pt(s):
    """'ab' -> (0, 1)"""
    return ord(s[0]) - 97, ord(s[1]) - 97


# ---------------- rules ----------------
def nbrs(p):
    x, y = p
    for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= q[0] < N and 0 <= q[1] < N:
            yield q


def group(b, p):
    c, seen, st, libs = b[p], {p}, [p], set()
    while st:
        q = st.pop()
        for r in nbrs(q):
            v = b.get(r)
            if v is None: libs.add(r)
            elif v == c and r not in seen: seen.add(r); st.append(r)
    return seen, libs


def play(b, c, p, ko):
    """New board and ko point, or raise if illegal."""
    if p is None:
        return b, None
    if p in b: raise ValueError(f'occupied {p}')
    if p == ko: raise ValueError(f'ko retake {p}')
    b = dict(b); b[p] = c
    opp = 'O' if c == 'X' else 'X'
    caps = set()
    for q in nbrs(p):
        if b.get(q) == opp:
            g, l = group(b, q)
            if not l: caps |= g
    for q in caps: del b[q]
    g, l = group(b, p)
    if not l: raise ValueError(f'suicide {p}')
    nko = next(iter(caps)) if len(caps) == 1 and len(g) == 1 and len(l) == 1 else None
    return b, nko


# ---------------- notes ----------------
NOTES = []


class Moves(list):
    """A move list that remembers the diagram it was read from."""
    src = None


def _tag(moves, page, n, first=1):
    m = Moves(moves)
    m.src = (page, n, first)
    return m


class Line:
    def __init__(self, *parts, end=None, checks=()):
        """parts: move lists (from seq) played one after another. `checks`:
        (index into parts, page, diagram) whose base must equal the position
        reached before that part. `end`: comment shown when the line is over."""
        self.parts, self.end, self.checks = parts, end, checks

    def moves(self):
        return [m for p in self.parts for m in p]


def note(**kw):
    NOTES.append(kw)


def stones_eq(a, b):
    return {p: c for p, c in a.items()} == {p: c for p, c in b.items()}


def start(nt):
    """The note's starting position: its base diagram plus any `pre` moves."""
    b, ko = base(*nt['base']), None
    for c, p in nt.get('pre', ()):
        b, ko = play(b, c, p, ko)
    return b


def validate(nt):
    b0 = start(nt)
    for li, ln in enumerate(nt['lines']):
        b, ko = b0, None
        tm = nt['to_move']
        idx = 0
        for pi, part in enumerate(ln.parts):
            src = getattr(part, 'src', None)
            if src:
                page, n, first = src
                want = dict(base(page, n))
                for k, (c, p) in numbered(page, n).items():
                    if k < first: want[p] = c
                shown = set(cells(page, n))
                if first == 10 ** 9:  # lettered move after a numbered sequence: numbered stones may be captured
                    shown -= {p for c, p in numbered(page, n).values()}
                diff = sorted((p, b.get(p), want.get(p)) for p in shown if b.get(p) != want.get(p))
                if diff:
                    raise ValueError(f"{nt['title']}: line {li} part {pi}: position differs from {page} D{n}: {diff}")
            for (ci, page, n) in ln.checks:
                if ci == pi and not stones_eq(b, base(page, n)):
                    diff = {p: (b.get(p), base(page, n).get(p)) for p in set(b) | set(base(page, n)) if b.get(p) != base(page, n).get(p)}
                    raise ValueError(f"{nt['title']}: line {li} part {pi}: position differs from {page} D{n}: {diff}")
            for c, p in part:
                if c != tm:
                    raise ValueError(f"{nt['title']}: line {li} move {idx + 1}: expected {tm} got {c} at {p}")
                try:
                    b, ko = play(b, c, p, ko)
                except ValueError as e:
                    raise ValueError(f"{nt['title']}: line {li} move {idx + 1}: {e}")
                tm = 'O' if tm == 'X' else 'X'
                idx += 1
    return True


def crop(nt):
    b0 = start(nt)
    pts = set(b0) | {p for ln in nt['lines'] for c, p in ln.moves() if p}
    pts |= set(nt.get('extra_pts', ()))
    x0 = 0 if min(x for x, y in pts) <= 1 else min(x for x, y in pts) - 1
    y0 = 0 if min(y for x, y in pts) <= 1 else min(y for x, y in pts) - 1
    x1 = min(N - 1, max(x for x, y in pts) + 1)
    y1 = min(N - 1, max(y for x, y in pts) + 1)
    edges = ('T' if y0 == 0 else '') + ('L' if x0 == 0 else '') + ('B' if y1 == N - 1 else '') + ('R' if x1 == N - 1 else '')
    rows = [''.join(b0.get((x, y), '.') for x in range(x0, x1 + 1)) for y in range(y0, y1 + 1)]
    return rows, edges, (x0, y0)


def name(p, off):
    return '..' if p is None else chr(97 + p[0] - off[0]) + chr(97 + p[1] - off[1])


def tree(nt, off):
    """Merge lines into a trie and serialise it.
    seq := item*; item := move ['{' text '}'] | '(' seq ('|' seq)+ ')'"""
    root = {}
    order = []
    for ln in nt['lines']:
        node = root
        mv = ln.moves()
        for k, (c, p) in enumerate(mv):
            key = name(p, off)
            if key not in node:
                node[key] = {'kids': {}, 'end': None}
            if k == len(mv) - 1 and ln.end:
                node[key]['end'] = ln.end
            node = node[key]['kids']

    def clean(t):
        return t.replace('{', '(').replace('}', ')').replace('|', '/')

    def ser(node):
        items = []
        for key, v in node.items():
            s = key + ('{' + clean(v['end']) + '}' if v['end'] else '') + ser(v['kids'])
            items.append(s)
        if not items: return ''
        if len(items) == 1: return items[0]
        return '(' + '|'.join(items) + ')'
    return ser(root)


def build():
    rows = []
    seen = set()
    for nt in NOTES:
        validate(nt)
        r, edges, off = crop(nt)
        sol = tree(nt, off)
        key = (','.join(r), nt['to_move'])
        assert key not in seen, ('duplicate board+to_move', nt['title'])
        seen.add(key)
        assert nt['title'] not in {x['Title'] for x in rows}, nt['title']
        rows.append({
            'Title': nt['title'], 'Board': ','.join(r), 'Edges': edges,
            'ToMove': 'B' if nt['to_move'] == 'X' else 'W',
            'Player': 'B' if nt['player'] == 'X' else 'W',
            'Status': nt['status'], 'Prompt': nt['prompt'], 'Solution': sol,
            'Notes': nt.get('notes', ''),
            'Japanese': nt.get('japanese', ''),
            'Source': ' '.join(f'<a href="{DATA[pg]["url"]}">{pg}</a>' for pg in dict.fromkeys(nt.get('sources', [nt['base'][0]]))),
        })
    return rows
