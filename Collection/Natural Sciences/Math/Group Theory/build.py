"""Generate Group.tsv, a Cayley-table SVG per group in media/, and manifest.json's "media" map.

Every group of order 1 to 12, up to isomorphism (24 groups). Each group is built
concretely (integer tuples for abelian groups, permutations, or 2x2 complex
matrices), and the script checks that it has the stated order, satisfies its
presentation's relations, and is abelian exactly when its class says so. Fact 1
is computed (how many elements have each order, which alone tells all 24 apart);
the rest are written by hand.

Elements are listed in the normal form g1^i g2^j ... of the group's generators, so
the table shows the structure: cosets of the first generator's subgroup form blocks.

Run by anki_sync.py check/push (manifest.json's "build" key), or standalone.
"""

import cmath
import csv
import itertools
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Group.tsv")
MANIFEST = os.path.join(HERE, "manifest.json")
MEDIA = os.path.join(HERE, "media")

SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


# --- Concrete groups -------------------------------------------------------------

class Group:
    """A finite group given by generators (with letters and exponent ranges), so
    that every element is g1^i1 g2^i2 ... exactly once."""

    def __init__(self, identity, mul, gens, labels=None):
        self.e, self.mul = identity, mul
        self.gens = gens                      # [(letter, element, exponent range)]
        self.elements, self.names = [], []
        # The first generator varies fastest, so its cyclic subgroup comes first and
        # each coset of it is a contiguous block.
        for rev in itertools.product(*(range(n) for _, _, n in reversed(gens))):
            exps = rev[::-1]
            x, word = identity, ""
            for (letter, g, _), k in zip(gens, exps):
                x = self.mul(x, self.pow(g, k))
                if k:
                    word += letter + (str(k).translate(SUP) if k > 1 else "")
            self.elements.append(x)
            self.names.append(word or "e")
        if labels:
            self.names = [labels.get(n, n) for n in self.names]
        assert len(set(self.elements)) == len(self.elements), "normal form repeats an element"
        index = {x: i for i, x in enumerate(self.elements)}
        self.table = [[index[self.mul(x, y)] for y in self.elements] for x in self.elements]
        self.index = index

    def pow(self, g, k):
        x = self.e
        for _ in range(k):
            x = self.mul(x, g)
        return x

    def inv(self, g):
        return next(x for x in self.elements if self.mul(g, x) == self.e)

    def gen(self, letter):
        return next(g for l, g, _ in self.gens if l == letter)

    def order_of(self, g):
        k, x = 1, g
        while x != self.e:
            x, k = self.mul(x, g), k + 1
        return k

    def abelian(self):
        return all(self.mul(x, y) == self.mul(y, x) for x in self.elements for y in self.elements)


def abelian(*ns):
    """Z_n1 x Z_n2 x ..., generators a, b, c."""
    mul = lambda x, y: tuple((p + q) % n for p, q, n in zip(x, y, ns))
    gens = [("abc"[i], tuple(int(j == i) for j in range(len(ns))), n) for i, n in enumerate(ns)]
    return Group(tuple(0 for _ in ns), mul, gens)


def compose(p, q):
    """Permutation p after q."""
    return tuple(p[i] for i in q)


def dihedral(n):
    """Symmetries of a regular n-gon: rotation r, reflection s."""
    r = tuple((i + 1) % n for i in range(n))
    s = tuple((-i) % n for i in range(n))
    return Group(tuple(range(n)), compose, [("r", r, n), ("s", s, 2)])


def alternating4():
    x, y, t = (1, 0, 3, 2), (2, 3, 0, 1), (0, 2, 3, 1)   # (01)(23), (02)(13), (123)
    return Group((0, 1, 2, 3), compose, [("x", x, 2), ("y", y, 2), ("t", t, 3)])


def matmul(A, B):
    (a, b, c, d), (p, q, r, s) = A, B
    rnd = lambda z: complex(round(z.real, 9) + 0.0, round(z.imag, 9) + 0.0)
    return tuple(rnd(v) for v in (a * p + b * r, a * q + b * s, c * p + d * r, c * q + d * s))


def dicyclic(n, letters="ax", labels=None):
    """Dic_n (order 4n): a = diag(z, 1/z) with z a primitive 2n-th root of unity,
    x = [[0, -1], [1, 0]]. Dic_2 is the quaternion group."""
    z = cmath.exp(1j * cmath.pi / n)
    a = matmul((z, 0, 0, 1 / z), (1, 0, 0, 1))
    x = (0j, -1 + 0j, 1 + 0j, 0j)
    return Group((1 + 0j, 0j, 0j, 1 + 0j), matmul, [(letters[0], a, 2 * n), (letters[1], x, 2)], labels)


# --- The groups -------------------------------------------------------------------
# (name, group, presentation, class, [hand-written facts, at most 5], relations)
# relations: lambda G -> list of (lhs, rhs) elements that must be equal.

def rel_cyclic(n):
    return lambda G: [(G.pow(G.gen("a"), n), G.e)]


def rel_product(*ns):
    def rels(G):
        gs = [G.gen(l) for l in "abc"[:len(ns)]]
        out = [(G.pow(g, n), G.e) for g, n in zip(gs, ns)]
        out += [(G.mul(g, h), G.mul(h, g)) for g, h in itertools.combinations(gs, 2)]
        return out
    return rels


def rel_dihedral(n):
    def rels(G):
        r, s = G.gen("r"), G.gen("s")
        return [(G.pow(r, n), G.e), (G.pow(s, 2), G.e), (G.mul(G.mul(s, r), s), G.inv(r))]
    return rels


def rel_dicyclic(n, a="a", x="x"):
    def rels(G):
        A, X = G.gen(a), G.gen(x)
        return [(G.pow(A, 2 * n), G.e), (G.pow(X, 2), G.pow(A, n)),
                (G.mul(G.mul(X, A), G.inv(X)), G.inv(A))]
    return rels


def rel_a4(G):
    x, y, t = G.gen("x"), G.gen("y"), G.gen("t")
    ti = G.inv(t)
    return [(G.pow(x, 2), G.e), (G.pow(y, 2), G.e), (G.pow(t, 3), G.e), (G.mul(x, y), G.mul(y, x)),
            (G.mul(G.mul(t, x), ti), y), (G.mul(G.mul(t, y), ti), G.mul(x, y))]


def C(n):
    return f"C<sub>{n}</sub>"


def cyclic_pres(n):
    return f"⟨ a | a{str(n).translate(SUP)} = e ⟩"


def product_pres(n, m):
    return (f"⟨ a, b | a{str(n).translate(SUP)} = b{str(m).translate(SUP)} = e, ab = ba ⟩")


def dihedral_pres(n):
    return f"⟨ r, s | r{str(n).translate(SUP)} = s² = e, srs = r⁻¹ ⟩"


CYCLIC = "Cyclic (abelian)"
ABELIAN = "Abelian, not cyclic"
DIHEDRAL = "Dihedral (non-abelian)"

GROUPS = [
    ("Trivial group", abelian(1), "⟨ a | a = e ⟩", "Trivial (cyclic, abelian)", [
        "The only group with one element: just the identity",
        "The quotient G/G of any group G by itself",
        "Symmetry group of an object with no symmetry at all",
    ], rel_cyclic(1)),

    ("Cyclic group " + C(2), abelian(2), cyclic_pres(2), CYCLIC, [
        "The only group of order 2",
        "The numbers {1, −1} under multiplication",
        "Symmetry group of a shape with exactly one mirror line and no rotations",
        "The image of the sign map on permutations (even vs. odd)",
    ], rel_cyclic(2)),

    ("Cyclic group " + C(3), abelian(3), cyclic_pres(3), CYCLIC, [
        "The only group of order 3",
        "Rotations of an equilateral triangle (no flips)",
        "The cube roots of unity under multiplication",
        "The alternating group A<sub>3</sub>: even permutations of 3 objects",
    ], rel_cyclic(3)),

    ("Cyclic group " + C(4), abelian(4), cyclic_pres(4), CYCLIC, [
        "Rotations of a square (no flips)",
        "The fourth roots of unity {1, i, −1, −i} under multiplication",
        "The units {1, 2, 3, 4} mod 5 under multiplication",
        "The group of order 4 with an element of order 4",
    ], rel_cyclic(4)),

    ("Klein four-group " + C(2) + " × " + C(2), abelian(2, 2), product_pres(2, 2), ABELIAN, [
        "The smallest non-cyclic group",
        "Symmetries of a non-square rectangle: identity, two mirror flips, half-turn",
        "The units {1, 3, 5, 7} mod 8 under multiplication",
        "The double transpositions with e: a normal subgroup of A<sub>4</sub> and S<sub>4</sub>",
    ], rel_product(2, 2)),

    ("Cyclic group " + C(5), abelian(5), cyclic_pres(5), CYCLIC, [
        "The only group of order 5",
        "Rotations of a regular pentagon (no flips)",
        "The integers mod 5 under addition",
    ], rel_cyclic(5)),

    ("Cyclic group " + C(6), abelian(6), cyclic_pres(6), CYCLIC, [
        "The only abelian group of order 6",
        "Isomorphic to C<sub>2</sub> × C<sub>3</sub>, by the Chinese remainder theorem",
        "The units mod 7 under multiplication",
        "Rotations of a regular hexagon (no flips)",
    ], rel_cyclic(6)),

    ("Symmetric group S<sub>3</sub> ≅ D<sub>3</sub>", dihedral(3), dihedral_pres(3), DIHEDRAL, [
        "The smallest non-abelian group",
        "All permutations of 3 objects",
        "Symmetries of an equilateral triangle, flips included",
        "GL(2, F<sub>2</sub>): the invertible 2×2 matrices over the field with two elements",
    ], rel_dihedral(3)),

    ("Cyclic group " + C(7), abelian(7), cyclic_pres(7), CYCLIC, [
        "The only group of order 7",
        "Rotations of a regular heptagon (no flips)",
        "The integers mod 7 under addition",
    ], rel_cyclic(7)),

    ("Cyclic group " + C(8), abelian(8), cyclic_pres(8), CYCLIC, [
        "The only group of order 8 with an element of order 8",
        "Rotations of a regular octagon (no flips)",
        "The eighth roots of unity under multiplication",
    ], rel_cyclic(8)),

    (C(4) + " × " + C(2), abelian(4, 2), product_pres(4, 2), ABELIAN, [
        "The abelian group of order 8 whose largest element order is 4",
        "The units mod 15 under multiplication",
        "The units mod 16 under multiplication",
    ], rel_product(4, 2)),

    ("Elementary abelian group " + C(2) + "<sup>3</sup>", abelian(2, 2, 2),
     "⟨ a, b, c | a² = b² = c² = e, all commute ⟩", ABELIAN, [
        "3-bit strings under XOR: the vector space F<sub>2</sub><sup>3</sup>",
        "The units mod 24 under multiplication",
        "Symmetries of a rectangular box: mirror flips in its three midplanes and their combinations",
        "The group of order 8 in which every element is its own inverse",
    ], rel_product(2, 2, 2)),

    ("Dihedral group D<sub>4</sub>", dihedral(4), dihedral_pres(4), DIHEDRAL, [
        "Symmetries of a square, flips included",
        "A Sylow 2-subgroup of S<sub>4</sub>",
        "The upper unitriangular 3×3 matrices over F<sub>2</sub> (the Heisenberg group mod 2)",
    ], rel_dihedral(4)),

    ("Quaternion group Q<sub>8</sub>", dicyclic(2, "ij", {"e": "1", "i²": "−1", "i³": "−i", "ij": "k",
                                                            "i²j": "−j", "i³j": "−k"}),
     "⟨ i, j | i⁴ = e, i² = j², jij⁻¹ = i⁻¹ ⟩", "Non-abelian (Hamiltonian)", [
        "The unit quaternions {±1, ±i, ±j, ±k}",
        "The smallest non-abelian group in which every subgroup is normal",
        "A non-abelian group of order 8 that is not a semidirect product of smaller groups",
    ], rel_dicyclic(2, "i", "j")),

    ("Cyclic group " + C(9), abelian(9), cyclic_pres(9), CYCLIC, [
        "Rotations of a regular nonagon (no flips)",
        "The integers mod 9 under addition",
        "The group of order 9 with an element of order 9",
    ], rel_cyclic(9)),

    (C(3) + " × " + C(3), abelian(3, 3), product_pres(3, 3), ABELIAN, [
        "The vector space F<sub>3</sub><sup>2</sup> under addition",
        "Translations of a 3×3 grid that wraps around like a torus",
        "The group of order 9 with no element of order 9",
    ], rel_product(3, 3)),

    ("Cyclic group " + C(10), abelian(10), cyclic_pres(10), CYCLIC, [
        "Isomorphic to C<sub>2</sub> × C<sub>5</sub>",
        "The units mod 11 under multiplication",
        "Rotations of a regular decagon (no flips)",
    ], rel_cyclic(10)),

    ("Dihedral group D<sub>5</sub>", dihedral(5), dihedral_pres(5), DIHEDRAL, [
        "Symmetries of a regular pentagon, flips included",
        "The only non-abelian group of order 10",
        "Symmetries of an idealized five-armed starfish",
    ], rel_dihedral(5)),

    ("Cyclic group " + C(11), abelian(11), cyclic_pres(11), CYCLIC, [
        "The only group of order 11",
        "The integers mod 11 under addition",
        "Rotations of a regular hendecagon (no flips)",
    ], rel_cyclic(11)),

    ("Cyclic group " + C(12), abelian(12), cyclic_pres(12), CYCLIC, [
        "Clock arithmetic: hours on a 12-hour clock under addition",
        "Isomorphic to C<sub>4</sub> × C<sub>3</sub>",
        "Rotations of a regular dodecagon (no flips)",
    ], rel_cyclic(12)),

    (C(6) + " × " + C(2), abelian(6, 2), product_pres(6, 2), ABELIAN, [
        "Isomorphic to C<sub>2</sub> × C<sub>2</sub> × C<sub>3</sub>",
        "The units mod 21 under multiplication",
        "The non-cyclic abelian group of order 12",
    ], rel_product(6, 2)),

    ("Alternating group A<sub>4</sub>", alternating4(),
     "⟨ x, y, t | x² = y² = t³ = e, xy = yx, txt⁻¹ = y, tyt⁻¹ = xy ⟩", "Non-abelian", [
        "The even permutations of 4 objects",
        "Rotations of a regular tetrahedron",
        "Has no subgroup of order 6: the smallest counterexample to the converse of Lagrange's theorem",
        "The semidirect product (C<sub>2</sub> × C<sub>2</sub>) ⋊ C<sub>3</sub>",
    ], rel_a4),

    ("Dihedral group D<sub>6</sub>", dihedral(6), dihedral_pres(6), DIHEDRAL, [
        "Symmetries of a regular hexagon, flips included",
        "Isomorphic to S<sub>3</sub> × C<sub>2</sub>",
        "Symmetries of an idealized snowflake",
    ], rel_dihedral(6)),

    ("Dicyclic group Dic<sub>3</sub>", dicyclic(3), "⟨ a, x | a⁶ = e, x² = a³, xax⁻¹ = a⁻¹ ⟩",
     "Non-abelian (dicyclic)", [
        "The semidirect product C<sub>3</sub> ⋊ C<sub>4</sub>, with C<sub>4</sub> acting by inversion",
        "The binary dihedral group of order 12: the preimage of the dihedral rotation group of order 6 under SU(2) → SO(3)",
        "The non-abelian group of order 12 with exactly one element of order 2",
    ], rel_dicyclic(3)),
]


# --- Facts, table, output ---------------------------------------------------------

def order_fact(G):
    counts = sorted(Counter(G.order_of(x) for x in G.elements).items())
    parts = [f"{n} of order {k}" for k, n in counts]
    return "Elements by order: " + ", ".join(parts)


def table_svg(G):
    n = len(G.elements)
    cell = 34
    size = cell * (n + 1)
    hue = lambda k: round(330 * (k - 1) / max(n - 2, 1))   # e is gray; the rest spread over the wheel
    fill = lambda k: "#eeeeee" if k == 0 else f"hsl({hue(k)}, 55%, 62%)"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
           f'width="{size}" height="{size}" font-family="Helvetica, Arial, sans-serif" '
           f'font-size="{13 if n > 1 else 15}" text-anchor="middle" dominant-baseline="central">',
           f'<rect width="{size}" height="{size}" fill="#1a1a1a"/>']

    def text(x, y, label, color):
        out.append(f'<text x="{x + cell / 2}" y="{y + cell / 2}" fill="{color}">{label}</text>')

    out.append(f'<rect width="{cell}" height="{cell}" fill="#1a1a1a"/>')
    text(0, 0, "·", "#cccccc")
    for i, name in enumerate(G.names):
        text((i + 1) * cell, 0, name, "#e6e6e6")
        text(0, (i + 1) * cell, name, "#e6e6e6")
    for i, row in enumerate(G.table):
        for j, k in enumerate(row):
            x, y = (j + 1) * cell, (i + 1) * cell
            out.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill(k)}" '
                       f'stroke="#1a1a1a" stroke-width="1"/>')
            text(x, y, G.names[k], "#111111")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def media_name(name):
    plain = re.sub(r"<[^>]+>", "", name)
    plain = plain.translate(str.maketrans({"×": "x", "≅": "", "²": "2", "³": "3"}))
    return "group_" + re.sub(r"[^a-z0-9]+", "_", plain.lower()).strip("_") + ".svg"


def main():
    names = [g[0] for g in GROUPS]
    assert len(set(names)) == len(names), "duplicate group name"
    os.makedirs(MEDIA, exist_ok=True)
    rows, media = [], {}
    expected = {1: 1, 2: 1, 3: 1, 4: 2, 5: 1, 6: 2, 7: 1, 8: 5, 9: 2, 10: 2, 11: 1, 12: 5}
    assert Counter(len(g[1].elements) for g in GROUPS) == Counter(expected), "wrong number of groups per order"
    profiles = set()
    for name, G, pres, cls, facts, rels in GROUPS:
        assert len(facts) <= 5, f"{name}: too many facts"
        for lhs, rhs in rels(G):
            assert lhs == rhs, f"{name}: a relation of its presentation fails"
        assert G.abelian() == ("abelian" in cls.lower() and "non-abelian" not in cls.lower()), \
            f"{name}: class says abelian={not G.abelian()}"
        fact1 = order_fact(G)
        assert fact1 not in profiles, f"{name}: element orders don't identify it"
        profiles.add(fact1)
        img = media_name(name)
        with open(os.path.join(MEDIA, img), "w", encoding="utf-8") as fh:
            fh.write(table_svg(G))
        media[img] = f"media/{img}"
        all_facts = [fact1, *facts]
        rows.append([name, f'<img src="{img}">', pres, f"Order {len(G.elements)}", cls,
                     *all_facts, *[""] * (6 - len(all_facts)), ""])
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["Name", "Table", "Presentation", "Order", "Class",
                         *[f"Fact {i}" for i in range(1, 7)], "Tags"])
        writer.writerows(rows)
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["media"] = media
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {len(rows)} groups to {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
