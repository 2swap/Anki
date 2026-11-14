"""Build the Export Portfolios deck.

Data/exports_2023.json  - per-country HS4 export values (OEC / BACI HS92, 2023), from Data/fetch_tradle.py
Data/products.json      - HS4 id -> product name / HS2 / section
Data/notes.md           - authored back-of-card notes: "## <ISO2>" then markdown bullets

Writes media/exp_<iso2>.png (treemaps, skipped when up to date) and
Portfolio.tsv.
"""
import html, json, os, re
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "Data")
MEDIA = os.path.join(HERE, "media")
TSV = os.path.join(HERE, "Portfolio.tsv")
W, H = 1200, 800
FONT = "/usr/share/fonts/noto/NotoSans-Regular.ttf"
FONT_B = "/usr/share/fonts/noto/NotoSans-Bold.ttf"

SECTION_COLORS = {
    1: "#E9C46A",   # Animal Products
    2: "#8CC152",   # Vegetable Products
    3: "#C9B458",   # Animal and Vegetable Bi-Products
    4: "#5DBB8A",   # Foodstuffs
    5: "#8D6E63",   # Mineral Products
    6: "#E56B9F",   # Chemical Products
    7: "#B39DDB",   # Plastics and Rubbers
    8: "#C08552",   # Animal Hides
    9: "#A1887F",   # Wood Products
    10: "#D7CCA1",  # Paper Goods
    11: "#4FC3F7",  # Textiles
    12: "#26A69A",  # Footwear and Headwear
    13: "#B0A99F",  # Stone And Glass
    14: "#F4B400",  # Precious Metals
    15: "#E07A5F",  # Metals
    16: "#5C7CBA",  # Machines
    17: "#8E6CC3",  # Transportation
    18: "#F28E5C",  # Instruments
    19: "#6D6D6D",  # Weapons
    20: "#C7A2C9",  # Miscellaneous
    21: "#9E9D24",  # Arts and Antiques
}


def squarify(values, x, y, w, h):
    """Squarified treemap layout. values sorted descending, all > 0. Returns [(x, y, w, h)]."""
    total = sum(values)
    if total <= 0 or not values:
        return []
    scale = w * h / total
    areas = [v * scale for v in values]
    rects = []
    i = 0
    while i < len(areas):
        short = min(w, h)
        row = [areas[i]]
        j = i + 1

        def worst(r):
            s = sum(r)
            return max(max(s * s / (short * short * a), short * short * a / (s * s)) for a in r)

        while j < len(areas) and worst(row + [areas[j]]) <= worst(row):
            row.append(areas[j])
            j += 1
        s = sum(row)
        if w >= h:  # lay row out as a column on the left
            cw = s / h
            cy = y
            for a in row:
                rects.append((x, cy, cw, a / cw))
                cy += a / cw
            x += cw
            w -= cw
        else:  # lay row out along the top
            rh = s / w
            cx = x
            for a in row:
                rects.append((cx, y, a / rh, rh))
                cx += a / rh
            y += rh
            h -= rh
        i = j
    return rects


_fonts = {}


def font(size, bold=False):
    k = (size, bold)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(FONT_B if bold else FONT, size)
    return _fonts[k]


def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for word in text.split():
        t = (cur + " " + word).strip()
        if draw.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def label(draw, rect, name, pct):
    x, y, w, h = rect
    pad = 4
    if w < 38 or h < 20:
        return
    for size in (26, 22, 18, 15, 13, 11):
        f = font(size, bold=True)
        fp = font(max(size - 2, 10))
        lines = wrap(draw, name, f, w - 2 * pad)
        lh = size * 1.18
        need = lh * len(lines) + (size + 2)
        if all(draw.textlength(l, font=f) <= w - 2 * pad for l in lines) and need <= h - 2 * pad:
            ty = y + pad
            for l in lines:
                draw.text((x + pad, ty), l, font=f, fill="white", stroke_width=max(1, size // 9), stroke_fill=(0, 0, 0, 120))
                ty += lh
            draw.text((x + pad, ty), pct, font=fp, fill="white", stroke_width=1, stroke_fill=(0, 0, 0, 120))
            return


def fmt_pct(s):
    return f"{s * 100:.1f}%" if s >= 0.001 else "<0.1%"


def render(country, products, out):
    items = [(products[str(pid)], v) for pid, v in country["products"]]
    total = sum(v for _, v in items)
    by_sec = {}
    for p, v in items:
        by_sec.setdefault(p["section_id"], []).append((p, v))
    secs = sorted(by_sec.items(), key=lambda kv: -sum(v for _, v in kv[1]))
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img, "RGBA")
    sec_rects = squarify([sum(v for _, v in ps) for _, ps in secs], 0, 0, W, H)
    for (sid, ps), (sx, sy, sw, sh) in zip(secs, sec_rects):
        color = SECTION_COLORS[sid]
        ps.sort(key=lambda pv: -pv[1])
        rects = squarify([v for _, v in ps], sx, sy, sw, sh)
        for (p, v), r in zip(ps, rects):
            x, y, w, h = r
            draw.rectangle([x, y, x + w, y + h], fill=color, outline=(255, 255, 255, 140), width=1)
        for (p, v), r in zip(ps, rects):
            label(draw, r, p["hs4"], fmt_pct(v / total))
        draw.rectangle([sx, sy, sx + sw, sy + sh], outline="white", width=3)
    img.quantize(colors=128, method=Image.Quantize.MEDIANCUT).save(out, optimize=True)


def fmt_usd(v):
    for div, suf in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
        if v >= div:
            x = v / div
            return f"${x:.3g}{suf}" if x < 100 else f"${x:.0f}{suf}"
    return f"${v:.0f}"


def md_inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
    return s


def parse_notes(path):
    notes, cur, buf = {}, None, []

    def flush():
        if cur:
            lis = [f"<li>{md_inline(b)}</li>" for b in buf]
            notes[cur] = "<ul>" + "".join(lis) + "</ul>"

    for line in open(path, encoding="utf-8"):
        line = line.rstrip()
        m = re.match(r"^## (\w\w)\b", line)
        if m:
            flush()
            cur, buf = m.group(1), []
        elif line.startswith("- "):
            buf.append(line[2:])
        elif line.startswith("  ") and buf:  # continuation line
            buf[-1] += " " + line.strip()
    flush()
    return notes


def main():
    exports = json.load(open(os.path.join(DATA, "exports_2023.json"), encoding="utf-8"))
    products = json.load(open(os.path.join(DATA, "products.json"), encoding="utf-8"))
    notes_path = os.path.join(DATA, "notes.md")
    notes = parse_notes(notes_path) if os.path.exists(notes_path) else {}
    os.makedirs(MEDIA, exist_ok=True)
    os.makedirs(os.path.dirname(TSV), exist_ok=True)
    deps = max(os.path.getmtime(__file__), os.path.getmtime(os.path.join(DATA, "exports_2023.json")))
    rows, rendered = [], 0
    for code, c in exports.items():
        png = f"exp_{code.lower()}.png"
        out = os.path.join(MEDIA, png)
        if not os.path.exists(out) or os.path.getmtime(out) < deps:
            render(c, products, out)
            rendered += 1
        total = sum(v for _, v in c["products"])
        rows.append([c["name"], f'<img src="{png}">', fmt_usd(total), notes.get(code, ""), "exports"])
    missing = [exports[c]["name"] for c in exports if c not in notes]
    with open(TSV, "w", encoding="utf-8") as fh:
        fh.write("Country\tTreemap\tTotal\tNotes\tTags\n")
        for r in rows:
            fh.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in r) + "\n")
    print(f"{len(rows)} notes, {rendered} treemaps rendered, {len(missing)} without notes")


if __name__ == "__main__":
    main()
