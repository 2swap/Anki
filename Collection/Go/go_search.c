/* Life-and-death search core for go_tsumego.py (loaded via ctypes).
 *
 * Board: W*H cells, row-major, chars '.', 'X', 'O'. The top of the crop (and the
 * left, unless open_left) are board edges; beyond the right and bottom is open board (a liberty that
 * nobody plays). Moves are restricted to the cells listed in `region`.
 *
 * kills(): 1 iff the attacker can capture the stone at `target` within `depth`
 * plies, where `km` ('X'/'O') may retake a ko immediately and the defender
 * survives on two consecutive passes or when the depth runs out.
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define MAXC 256
#define TTBITS 22
#define TTSIZE (1u << TTBITS)

static int openleft, W, H, N, nregion, region[MAXC], target;
static char A, D;
static uint64_t zob[MAXC][2], zko[MAXC + 1], zturn, zpass, zkm;

typedef struct { uint64_t key; int8_t win; int8_t depth; int16_t best; } Entry;
static Entry *tt;

static uint64_t rng = 88172645463325252ull;
static uint64_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return rng; }

/* neighbour index, or -1 for a board edge, -2 for open board */
static int nb(int i, int k) {
    int x = i % W, y = i / W;
    switch (k) {
    case 0: x++; break;
    case 1: x--; break;
    case 2: y++; break;
    default: y--; break;
    }
    if (y < 0) return -1;
    if (x < 0) return openleft ? -2 : -1;
    if (x >= W || y >= H) return -2;
    return y * W + x;
}

static int mark[MAXC], gen = 1;

/* stones of the group at i into out[], returns count; *libs = number of liberties (capped) */
static int group(const char *b, int i, int *out, int *libs) {
    int stack[MAXC], sp = 0, n = 0, l = 0;
    char c = b[i];
    gen += 2;
    stack[sp++] = i; mark[i] = gen;
    while (sp) {
        int p = stack[--sp];
        out[n++] = p;
        for (int k = 0; k < 4; k++) {
            int q = nb(p, k);
            if (q == -1) continue;
            if (q == -2) { l++; continue; }
            if (b[q] == '.') { if (mark[q] != gen + 1) { mark[q] = gen + 1; l++; } }
            else if (b[q] == c && mark[q] != gen) { mark[q] = gen; stack[sp++] = q; }
        }
    }
    *libs = l;
    return n;
}

/* play c at m on b (in place). Returns 0 if illegal (b unchanged), else 1, with *ko set. */
static int play(char *b, int m, char c, int *ko, uint64_t *h) {
    if (b[m] != '.') return 0;
    char o = c == 'X' ? 'O' : 'X';
    int stones[MAXC], libs, ncap = 0, lastcap = -1;
    b[m] = c;
    uint64_t hh = *h ^ zob[m][c == 'O'];
    for (int k = 0; k < 4; k++) {
        int q = nb(m, k);
        if (q < 0 || b[q] != o) continue;
        int n = group(b, q, stones, &libs);
        if (!libs) {
            for (int j = 0; j < n; j++) { b[stones[j]] = '.'; hh ^= zob[stones[j]][o == 'O']; }
            ncap += n; lastcap = stones[0];
        }
    }
    int n = group(b, m, stones, &libs);
    if (!libs) { b[m] = '.'; return 0; }  /* suicide (no captures possible here) */
    *ko = (ncap == 1 && n == 1 && libs == 1) ? lastcap : -1;
    *h = hh;
    return 1;
}

/* Benson's algorithm: 1 iff the defender chain containing `target` is
 * unconditionally alive (pass-alive). Regions touching the open board beyond
 * the crop never count as eyes. */
static int benson(const char *b) {
    int chain[MAXC], region[MAXC], nch = 0, nrg = 0, stack[MAXC];
    for (int i = 0; i < N; i++) chain[i] = region[i] = -1;
    int ropen[MAXC] = {0};
    for (int i = 0; i < N; i++) {
        int isD = b[i] == D;
        if ((isD ? chain[i] : region[i]) >= 0) continue;
        int id = isD ? nch++ : nrg++, sp = 0;
        if (isD) chain[i] = id; else region[i] = id;
        stack[sp++] = i;
        while (sp) {
            int p = stack[--sp];
            for (int k = 0; k < 4; k++) {
                int q = nb(p, k);
                if (q == -1) continue;
                if (q == -2) { if (!isD) ropen[id] = 1; continue; }
                if ((b[q] == D) != isD) continue;
                int *lab = isD ? chain : region;
                if (lab[q] < 0) { lab[q] = id; stack[sp++] = q; }
            }
        }
    }
    if (nch > 64) return 0;  /* masks below hold 64 chains; just skip the shortcut */
    /* vital[r]: chains for which every empty point of region r is a liberty; adj[r]: bordering chains */
    uint64_t vital[MAXC], adj[MAXC];
    for (int r = 0; r < nrg; r++) { vital[r] = ~0ull; adj[r] = 0; }
    for (int i = 0; i < N; i++) {
        int r = region[i];
        if (r < 0) continue;
        uint64_t touch = 0;
        for (int k = 0; k < 4; k++) {
            int q = nb(i, k);
            if (q >= 0 && chain[q] >= 0) touch |= 1ull << chain[q];
        }
        adj[r] |= touch;
        if (b[i] == '.') vital[r] &= touch;
    }
    uint64_t alive = nch == 64 ? ~0ull : (1ull << nch) - 1, active = 0;
    for (int r = 0; r < nrg; r++) if (!ropen[r]) vital[r] &= adj[r]; else vital[r] = 0;
    for (int changed = 1; changed;) {
        changed = 0;
        for (int c = 0; c < nch; c++) {
            if (!(alive >> c & 1)) continue;
            int n = 0;
            for (int r = 0; r < nrg && n < 2; r++) if (vital[r] >> c & 1) n++;
            if (n < 2) { alive &= ~(1ull << c); changed = 1; }
        }
        for (int r = 0; r < nrg; r++)
            if (vital[r] && (adj[r] & ~alive)) { vital[r] = 0; changed = 1; }
    }
    (void)active;
    return alive >> chain[target] & 1;
}

static uint64_t nodes;

static int search(const char *b, uint64_t h, char tomove, int ko, char km, int passes, int depth) {
    if (b[target] != D) return 1;
    if (depth <= 0 || benson(b)) return 0;
    if (passes >= 2) {
        /* The defender stopped here. If the attacker could still capture by
         * starting a ko only it can start (e.g. bent four in the corner), the
         * attacker picks the moment after removing ko threats: dead. */
        if (km == D) return search(b, h, A, -1, A, 0, depth);
        return 0;
    }
    uint64_t key = h ^ (tomove == 'O' ? zturn : 0) ^ zko[ko < 0 ? MAXC : ko]
                 ^ (passes ? zpass : 0) ^ (km == 'O' ? zkm : 0);
    Entry *e = &tt[key & (TTSIZE - 1)];
    int best = -1;
    if (e->key == key) {
        if (e->win) return 1;
        if (e->depth >= depth) return 0;
        best = e->best;
    }
    nodes++;
    int want = tomove == A;
    int result = !want, found = -1;
    char nb2[MAXC];
    char opp = tomove == 'X' ? 'O' : 'X';
    /* move order: TT best move first, then region order, then pass (index nregion) */
    for (int t = -1; t <= nregion; t++) {
        int m;
        if (t == -1) { if (best < 0) continue; m = best; }
        else if (t == nregion) m = -1;
        else { m = region[t]; if (m == best) continue; }
        int r;
        if (m == -1) {
            r = search(b, h, opp, -1, km, passes + 1, depth - 1);
        } else {
            if (m == ko && km != tomove) continue;
            memcpy(nb2, b, N);
            int nko; uint64_t nh = h;
            if (!play(nb2, m, tomove, &nko, &nh)) continue;
            r = search(nb2, nh, opp, nko, km, 0, depth - 1);
        }
        if (r == want) { result = want; found = m; break; }
    }
    e = &tt[key & (TTSIZE - 1)];
    int same = e->key == key, oldbest = same ? e->best : -1;
    if (result || !same || e->depth <= depth) {
        e->key = key; e->win = result; e->depth = depth;
        e->best = found >= 0 ? found : oldbest;
    }
    return result;
}

/* ---- API ---- */
void setup(int w, int h, const int *reg, int nreg, int tgt, char attacker, int open_left) {
    openleft = open_left;
    W = w; H = h; N = w * h; nregion = nreg; target = tgt;
    memcpy(region, reg, nreg * sizeof(int));
    A = attacker; D = attacker == 'X' ? 'O' : 'X';
    if (!tt) {
        tt = calloc(TTSIZE, sizeof(Entry));
        for (int i = 0; i < MAXC; i++) { zob[i][0] = rnd(); zob[i][1] = rnd(); zko[i] = rnd(); }
        zko[MAXC] = 0; zturn = rnd(); zpass = rnd(); zkm = rnd();
    }
    memset(tt, 0, TTSIZE * sizeof(Entry));
}

int kills(const char *board, char tomove, int ko, char km, int passes, int depth) {
    char b[MAXC];
    memcpy(b, board, N);
    uint64_t h = 0;
    for (int i = 0; i < N; i++)
        if (b[i] == 'X') h ^= zob[i][0]; else if (b[i] == 'O') h ^= zob[i][1];
    return search(b, h, tomove, ko, km, passes, depth);
}

uint64_t node_count(void) { return nodes; }
