"""Decode saved Sensei's Library pages into Data/sldata.json.

Usage: python3 Data/extract.py [~/carpenter]

Save each page with "Web page, complete". Every diagram on a page carries its
position as text (a hidden "boarddata" field: '.', 'X', 'O', ',' hoshi, '?'
outside, rows of width+1), but move numbers, letters and markers exist only in
the PNG. The PNGs are drawn on a fixed 23-pixel grid from fixed glyphs, so each
cell is matched exactly against glyphs.json (thresholded cell bitmap -> label:
'.', 'X', 'O', 'B3', 'W4', 'a', '.(c)' circle, '(s)' square, '(t)' triangle,
'(x)' cross). An unknown glyph becomes '?'; label it in glyphs.json.

Output: {page title: {url, diagrams: {n: {caption, grid, edges, off}}}}, where
grid is rows of labels for the cropped image, off is its offset on the board and
edges says which sides of the crop are real board edges.
"""
import glob, html, json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GLYPHS = json.load(open(os.path.join(HERE, 'glyphs.json')))
DIAGRAM = r'(?s)<div class="diagram"(?:(?!<div class="diagram").)*?</form></div>'


def cell(im, i, j):
    cx, cy = 13 + 23 * i, 13 + 23 * j
    box = im.crop((cx - 10, cy - 10, cx + 11, cy + 11)).convert('L')
    px = box.load()
    ring = [px[10 + dx, 10 + dy] for dx, dy in ((7, 0), (-7, 0), (0, 7), (0, -7), (5, 5), (-5, 5), (5, -5), (-5, -5))]
    return box, sum(ring) / len(ring)


def colour(avg):
    return 'X' if avg < 130 else 'O' if avg > 160 else '.'


def label(box):
    bits = ''.join('1' if v < 128 else '0' for v in box.getdata())
    lab = GLYPHS.get(format(int(bits, 2), 'x'), '?')
    if lab == 'X':
        # a grey circle on a black stone is lost by the threshold; look at the centre
        if max(box.getpixel((x, y)) for x in range(4, 17) for y in range(4, 17) if (x - 10) ** 2 + (y - 10) ** 2 <= 36) > 64:
            return 'X(c)'
    return lab


def decode(png, bd, w):
    """Labels of every cell, the crop's offset on the board and its real edges."""
    im = Image.open(png).convert('RGB')
    n, m = (im.size[0] - 26) // 23 + 1, (im.size[1] - 26) // 23 + 1
    rows = [bd[k * (w + 1):k * (w + 1) + w] for k in range(len(bd) // (w + 1))]
    bh = len(rows)
    pc = [[colour(cell(im, i, j)[1]) for i in range(n)] for j in range(m)]
    best = None
    for oy in range(0, bh - m + 1):
        for ox in range(0, w - n + 1):
            score = sum(rows[oy + j][ox + i].replace('?', '.').replace(',', '.') == pc[j][i] for j in range(m) for i in range(n))
            if best is None or score > best[0]:
                best = (score, ox, oy)
    _, ox, oy = best
    grid = [[label(cell(im, i, j)[0]) for i in range(n)] for j in range(m)]
    edges = ''.join(e for e, c in (('T', oy == 0), ('B', oy + m == bh), ('L', ox == 0), ('R', ox + n == w)) if c)
    return grid, edges, (ox, oy)


def main(src):
    pages = {}
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(src), '*.html'))):
        s = open(f, encoding='utf-8', errors='replace').read()
        d = os.path.dirname(f)
        title = os.path.basename(f).replace(" at Sensei's Library.html", '')
        mu = re.search(r'\?edit=([^"&]+)', s)
        diags = {}
        for n, m in enumerate(re.finditer(DIAGRAM, s), 1):
            p = m.group(0)
            if 'name="boarddata"' not in p:
                continue
            cap = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'(?s)</a><form[^>]*>(.*?)<input', p).group(1))).strip()
            png = os.path.join(d, re.search(r'src="\./([^"]+\.png)"', p).group(1))
            bd = re.search(r'name="boarddata" value="([^"]*)"', p).group(1)
            w = int(re.search(r'name="width" value="(\d+)"', p).group(1))
            grid, edges, off = decode(png, bd, w)
            diags[n] = {'caption': cap, 'grid': grid, 'edges': edges, 'off': off}
        pages[title] = {'url': 'https://senseis.xmp.net/?' + mu.group(1), 'diagrams': diags}
        unknown = [k for k, v in diags.items() if any('?' in c for r in v['grid'] for c in r)]
        if unknown:
            print(f'{title}: unknown glyphs in diagram(s) {unknown}')
    json.dump(pages, open(os.path.join(HERE, 'sldata.json'), 'w'))
    print(f'{len(pages)} pages, {sum(len(p["diagrams"]) for p in pages.values())} diagrams')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '~/carpenter')
