"""Verify corner tsumego by exhaustive search and add them as interactive "Go Tsumego" cards.

Usage:
  python3 go_tsumego.py check  spec.json [name-substring]  # print boards, statuses, solution trees
  python3 go_tsumego.py add    spec.json [name-substring]  # also add the notes to Anki
  python3 go_tsumego.py update spec.json [name-substring]  # refresh fields of matching notes

spec.json:
{
  "deck": "Go",
  "problems": [{
    "name": "L+1 group (leg on the long side)",
    "black": "cb cc bd cd be",          # SGF points, aa = the top-left corner
    "white": "db dc dd ce de bf cf",
    "defender": "B",                     # colour of the group in question
    "player": "W",                       # colour the person plays
    "goal": "kill" | "live" | "ko",      # what the player achieves ("ko": best is a ko)
    "edges": "TL",                       # optional: real board edges of the crop (default TL;
                                         # "T" for a side position, open on the left)
    "shift": [-3, 0],                    # optional: move all stones (e.g. side shapes to the crop's left)
    "first": "bb",                       # optional: computer opens at this point, or
                                         # "auto:N" = N cards, one per most testing opening
    "prompt": "White to kill",           # optional
    "notes": "...",                      # shown on the back
    "japanese": "カギ形 (kagigata)",      # shown on the back (default: no standard name)
    "solution": "-be(ac-ba(bb))",        # optional: a line from the literature instead of
                                         # searching (every move is still checked for legality)
    "statuses": "ac:L,ad:D"              # with "solution": the first-move outcomes it
                                         # establishes (L lives, K ko, D dies)
  }]
}

Rules model: the crop's top and left are board edges; past its right and bottom
edges lies open board (a liberty nobody plays). Play is restricted to the empty
points enclosed with the defender, so attacker walls must seal that area.
Status is exhaustive: "kill" means the attacker captures even if the defender
wins every ko; "ko" means it only captures if the attacker wins the kos;
anything else (life, seki) counts as alive.
"""
import ctypes, json, os, subprocess, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_core():
    """Compile go_search.c into a temp dir (nothing is written next to this script)."""
    out = os.path.join(tempfile.gettempdir(), f'go_search_{os.getuid()}.so')
    src = os.path.join(HERE, 'go_search.c')
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        subprocess.run(['gcc', '-O2', '-shared', '-fPIC', '-o', out, src], check=True)
    lib = ctypes.CDLL(out)
    lib.setup.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int, ctypes.c_char, ctypes.c_int]
    lib.kills.argtypes = [ctypes.c_char_p, ctypes.c_char, ctypes.c_int, ctypes.c_char, ctypes.c_int, ctypes.c_int]
    lib.node_count.restype = ctypes.c_uint64
    return lib


CORE = load_core()

sys.setrecursionlimit(10000)
MAXD = 40  # search depth in plies
ACTIVE = None


def pt(s):
    return ord(s[0]) - 97, ord(s[1]) - 97


def name(m):
    return 'pass' if m is None else chr(97 + m[0]) + chr(97 + m[1])


class Problem:
    def __init__(self, spec):
        self.spec = spec
        stones = {}
        for c, key in (('X', 'black'), ('O', 'white')):
            for s in spec.get(key, '').split():
                x, y = pt(s)
                dx, dy = spec.get('shift', (0, 0))
                stones[(x + dx, y + dy)] = c
        self.edges = spec.get('edges', 'TL')
        self.W = max(x for x, y in stones) + 2
        self.H = max(y for x, y in stones) + 2
        b = ['.'] * (self.W * self.H)
        for (x, y), c in stones.items():
            b[y * self.W + x] = c
        self.board = ''.join(b)
        self.D = 'X' if spec['defender'] == 'B' else 'O'
        self.A = 'O' if self.D == 'X' else 'X'
        self.P = 'X' if spec['player'] == 'B' else 'O'
        self.target = next(p for p, c in stones.items() if c == self.D)
        # A literal (literature) solution needs no search area.
        self.region = [] if spec.get('solution') else self._region()
        self.cache = {}

    def at(self, b, x, y):
        if y < 0 or (x < 0 and 'L' in self.edges):
            return '#'                     # board edge
        if x < 0:
            return 'L'
        if x >= self.W or y >= self.H:
            return 'L'                     # open board beyond the crop
        return b[y * self.W + x]

    def _region(self):
        seen, stack, region = set(), [], set()
        for y in range(self.H):
            for x in range(self.W):
                if self.at(self.board, x, y) == self.D:
                    stack.append((x, y))
                    seen.add((x, y))
        while stack:
            x, y = stack.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                v = self.at(self.board, *q)
                if v == 'L':
                    raise SystemExit(f'{self.spec["name"]}: defender area leaks out of the crop at {q}; seal it')
                if v in '.' + self.D and q not in seen:
                    seen.add(q)
                    stack.append(q)
                    if v == '.':
                        region.add(q)
        return sorted(region, key=lambda p: (p[1], p[0]))

    # ---- rules ----
    def group(self, b, x, y):
        c = self.at(b, x, y)
        seen, stack, libs = {(x, y)}, [(x, y)], set()
        while stack:
            px, py = stack.pop()
            for q in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                v = self.at(b, *q)
                if v in '.L':
                    libs.add(q)
                elif v == c and q not in seen:
                    seen.add(q)
                    stack.append(q)
        return seen, libs

    def play(self, b, m, c):
        """(board, ko point) after colour c plays m, or None if illegal."""
        x, y = m
        if self.at(b, x, y) != '.':
            return None
        b = list(b)
        b[y * self.W + x] = c
        opp = 'O' if c == 'X' else 'X'
        caps = set()
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if self.at(b, *q) == opp:
                g, libs = self.group(b, *q)
                if not libs:
                    caps |= g
        for px, py in caps:
            b[py * self.W + px] = '.'
        g, libs = self.group(b, x, y)
        if not libs:
            return None
        ko = next(iter(caps)) if len(caps) == 1 and len(g) == 1 and len(libs) == 1 else None
        return ''.join(b), ko

    # ---- search ----
    def kills(self, b, tomove, ko, km, passes=0, d=MAXD):
        """True iff the attacker captures the target within d plies (iterative deepening)."""
        key = (b, tomove, ko, km, passes, d)
        if key not in self.cache:
            self.activate()
            k = -1 if ko is None else ko[1] * self.W + ko[0]
            r = False
            for dd in list(range(2 - passes % 2, d, 4)) + [d]:
                if CORE.kills(b.encode(), tomove.encode(), k, km.encode(), passes, dd):
                    r = True
                    break
            self.cache[key] = r
        return self.cache[key]

    def activate(self):
        global ACTIVE
        if ACTIVE is not self:
            reg = [y * self.W + x for x, y in self.region]
            CORE.setup(self.W, self.H, (ctypes.c_int * len(reg))(*reg), len(reg),
                       self.target[1] * self.W + self.target[0], self.A.encode(), 'L' not in self.edges)
            ACTIVE = self

    def status(self, b, tomove, ko=None):
        """'kill', 'ko' or 'live' with `tomove` to move."""
        if self.kills(b, tomove, ko, self.D):
            return 'kill'
        if self.kills(b, tomove, ko, self.A):
            return 'ko'
        return 'live'

    def dist(self, b, tomove, ko, km):
        """Plies the attacker needs to capture (for picking stubborn replies)."""
        for d in range(1, MAXD + 1):
            if self.kills(b, tomove, ko, km, 0, d):
                return d
        return MAXD + 1

    def moves(self, b, c, ko, km):
        for m in self.region:
            if m == ko and km != c:
                continue
            p = self.play(b, m, c)
            if p:
                yield m, p

    # ---- solution tree ----
    def good(self, st):
        g = self.spec['goal']
        return st == 'kill' if g == 'kill' else st == 'live' if g == 'live' else st in ('ko', 'kill')

    def settled(self, b, ko):
        """Player's goal holds even if the opponent gets two moves in a row."""
        P, O, g = self.P, ('O' if self.P == 'X' else 'X'), self.spec['goal']
        if self.at(b, *self.target) != self.D:
            return True
        km = self.D if g == 'kill' else self.A
        for m, p in list(self.moves(b, O, ko, km)) + [(None, (b, None))]:
            st = self.status(p[0], O, p[1])
            if not self.good(st):
                return False
        return True

    def tree(self, b, ko, depth=0):
        P = self.P
        O = 'O' if P == 'X' else 'X'
        goal = self.spec['goal']
        km = self.D if goal == 'kill' else self.A
        alts = []
        for m, p in self.moves(b, P, ko, km):
            st = self.status(p[0], O, p[1])
            if not self.good(st):
                continue
            node = {'move': m, 'reply': None, 'next': [], 'status': st}
            if goal == 'ko' and p[1] is not None:
                alts.append(node)              # the ko has started
                continue
            if self.settled(p[0], p[1]) or depth >= int(os.environ.get("TDEPTH", 2)):
                alts.append(node)
                continue
            # Computer's reply: the opponent's best result first, then the reply
            # that leaves the player the fewest correct answers, then the longest fight.
            best = None
            for om, q in self.moves(p[0], O, p[1], km):
                now = self.status(q[0], P, q[1])
                if not self.good(now):
                    continue  # cannot happen when the player's last move was correct
                kids = [mm for mm, qq in self.moves(q[0], P, q[1], km)
                        if self.good(self.status(qq[0], O, qq[1]))]
                if not kids:
                    continue  # the player must pass here; not a useful card line
                pref = (now == 'ko') if goal == 'ko' else 0
                score = (pref, -len(kids), self.dist(q[0], P, q[1], km) if goal != 'live' else 0)
                if best is None or score > best[0]:
                    best = (score, om, q)
            if best is None:
                alts.append(node)
                continue
            node['reply'] = best[1]
            q = best[2]
            if goal == 'ko' and q[1] is not None:
                alts.append(node)
                continue
            node['next'] = self.tree(q[0], q[1], depth + 1)
            alts.append(node)
        return alts

    def status_map(self, b, ko):
        """'xy:L,xy:K,...': what each legal player move at this position means for
        the defender's group (L lives, K ko, D dies), with the opponent to move."""
        O = 'O' if self.P == 'X' else 'X'
        out = []
        for m in self.region:
            if m == ko:
                continue
            p = self.play(b, m, self.P)
            if p:
                st = self.status(p[0], O, p[1])
                out.append(name(m) + ':' + {'kill': 'D', 'ko': 'K', 'live': 'L'}[st])
        return ','.join(out)

    def show(self, b=None):
        b = b or self.board
        for y in range(self.H):
            print('   ' + ' '.join(
                ('+' if (x, y) in self.region and b[y * self.W + x] == '.' else b[y * self.W + x])
                for x in range(self.W)))


def encode(alts):
    out = []
    for a in alts:
        s = name(a['move'])
        if a['reply']:
            s += '-' + name(a['reply'])
        if a['next']:
            s += '(' + encode(a['next']) + ')'
        out.append(s)
    return '|'.join(out)


def dump(alts, ind=0):
    for a in alts:
        print('      ' + '  ' * ind + f"{name(a['move'])} [{a['status']}]" +
              (f" -> {name(a['reply'])}" if a['reply'] else ''))
        dump(a['next'], ind + 1)


def ac(action, **params):
    req = json.dumps({'action': action, 'version': 6, 'params': params}).encode()
    r = json.load(urllib.request.urlopen('http://localhost:8765', req))
    if r['error']:
        raise RuntimeError(f'{action}: {r["error"]}')
    return r['result']


def first_moves(pr, n):
    """The computer's n most testing opening moves: the player's goal still holds,
    with the fewest correct answers (at least one)."""
    P, O = pr.P, ('O' if pr.P == 'X' else 'X')
    km = pr.D if pr.spec['goal'] == 'kill' else pr.A
    ranked = []
    for m, p in pr.moves(pr.board, O, None, km):
        if not pr.good(pr.status(p[0], P, p[1])):
            continue
        kids = [mm for mm, q in pr.moves(p[0], P, p[1], km) if pr.good(pr.status(q[0], O, q[1]))]
        if kids:
            ranked.append((len(kids), name(m)))
    ranked.sort()
    return [m for k, m in ranked[:n]]


def existing():
    """(Board, ToPlay, Solution) of every Go Tsumego note. Anki's own duplicate
    check only sees the first field, and a kill and a live card share a board."""
    notes = ac('notesInfo', notes=ac('findNotes', query='"note:Go Tsumego"'))
    return {tuple(n['fields'][f]['value'] for f in ('Board', 'ToPlay', 'Solution')): n['noteId'] for n in notes}


def solve(spec):
    pr = Problem(spec)
    print('=' * 60)
    print(spec['name'], f"({spec['player']} to {spec['goal']}; defender {spec['defender']})")
    pr.show()
    b, ko = pr.board, None
    first = spec.get('first')
    O = 'O' if pr.P == 'X' else 'X'
    for who in ('A', 'D'):
        c = pr.A if who == 'A' else pr.D
        print(f'   {"attacker" if who == "A" else "defender"} first: {pr.status(b, c)}')
    if first:
        b, ko = pr.play(b, pt(first), O)
        print(f'   computer first at {first}:')
        pr.show(b)
    t = pr.tree(b, ko)
    dump(t)
    if not t:
        print('   !! no move achieves the goal')
    smap = pr.status_map(b, ko)
    print('   Statuses:', smap)
    return pr, t, smap


def expand(problems):
    """'first': 'auto:N' becomes N problems, one per testing computer opening."""
    for p in problems:
        f = p.get('first', '')
        if f.startswith('auto'):
            n = int(f.split(':')[1]) if ':' in f else 1
            for m in first_moves(Problem(p), n):
                yield dict(p, first=m)
        else:
            yield p


def parse(s):
    """Solution string -> [(move or '', reply or None, children)] (same grammar as the card)."""
    i = 0

    def node():
        nonlocal i
        alts = []
        while True:
            mv = ''
            if s[i] != '-':
                mv, i = s[i:i + 2], i + 2
            reply = None
            if i < len(s) and s[i] == '-':
                reply, i = s[i + 1:i + 3], i + 3
            kids = []
            if i < len(s) and s[i] == '(':
                i += 1
                kids = node()
                assert s[i] == ')', s
                i += 1
            alts.append((mv, reply, kids))
            if i < len(s) and s[i] == '|':
                i += 1
                continue
            return alts

    return node()


def check_literal(spec):
    """A solution taken from the literature: replay every branch and insist that
    each move is legal (empty point, no suicide, no immediate ko retake)."""
    pr = Problem(spec)
    sol = spec['solution']
    print('=' * 60)
    print(spec['name'], '(literature line)')
    pr.show()
    P = pr.P
    O = 'O' if P == 'X' else 'X'

    def walk(alts, b, ko, path):
        for mv, reply, kids in alts:
            nb, nko, p2 = b, ko, path
            for m, c in ((mv, P), (reply, O)):
                if not m:
                    continue
                if pt(m) == nko:
                    raise SystemExit(f'{spec["name"]}: {" ".join(p2 + [m])} retakes a ko illegally')
                r = pr.play(nb, pt(m), c)
                if not r:
                    raise SystemExit(f'{spec["name"]}: illegal move {m} after {" ".join(p2) or "start"}')
                nb, nko = r
                p2 = p2 + [('B' if c == 'X' else 'W') + m]
            if kids:
                walk(kids, nb, nko, p2)
            else:
                print('   line ok:', ' '.join(p2))
                pr.show(nb)

    walk(parse(sol), pr.board, None, [])
    print('   Solution:', sol)
    return pr, sol


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    filt = sys.argv[3] if len(sys.argv) > 3 else ''
    spec = json.load(open(path))
    for p in expand(q for q in spec['problems'] if filt in q['name']):
        if p.get('solution'):
            pr, sol = check_literal(p)
            t, smap = True, p.get('statuses', '')   # literature: only the moves it discusses
        else:
            pr, t, smap = solve(p)
            sol = encode(t)
            if p.get('first'):
                sol = '-' + p['first'] + '(' + sol + ')'
        print('   Solution:', sol)
        if cmd not in ('add', 'update') or not t:
            continue
        rows = ','.join(pr.board[y * pr.W:(y + 1) * pr.W] for y in range(pr.H))
        fields = {'Board': rows, 'Edges': pr.edges, 'ToPlay': p['player'],
                  'Solution': sol, 'Prompt': p.get('prompt', ''),
                  'Notes': f"<b>{p['name']}</b><br>{p.get('notes', '')}",
                  'Japanese': p.get('japanese', 'No standard Japanese name'),
                  'Statuses': smap}
        nid = existing().get((rows, p['player'], sol))
        if nid:
            if cmd == 'update':
                ac('updateNoteFields', note={'id': nid, 'fields': fields})
                print('   updated', nid)
            else:
                print('   already in Anki, skipped')
        elif cmd == 'add':
            note = {'deckName': spec['deck'], 'modelName': 'Go Tsumego', 'tags': ['tsumego'],
                    'options': {'allowDuplicate': True}, 'fields': fields}
            print('   added', ac('addNote', note=note))
        else:
            print('   !! no matching note to update')


if __name__ == '__main__':
    main()
