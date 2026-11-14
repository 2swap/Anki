"""Generate the Standard Model deck's TSVs from the tables below.

Particle.tsv - one note per elementary particle, including
                                   what it decays into (or that it doesn't).
Group.tsv    - one note per group of particles (a
                                   classification, which particles feel each
                                   fundamental force, or a shared charge /
                                   spin / mass band).

Grid positions are "row,col" on the usual chart (4 rows x 5 columns):

         col 0  col 1  col 2   col 3  col 4
    row0   u      c      t       g      H
    row1   d      s      b       γ
    row2   e      μ      τ       Z
    row3   νe     νμ     ντ      W

The card templates carry the same symbol layout for drawing the grid; keep
them in sync if a position changes. Run by anki_sync.py check/push
(manifest.json's "build" key), or standalone.
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = HERE

QUARK_COLOR = "Yes: red, green or blue"
GLUON_COLOR = "Yes: a color and an anticolor"
NO_COLOR = "None"

# (name, symbol HTML, position, charge, spin, color charge, mass, massless?)
# Masses: PDG 2024 central values (quark masses are scheme-dependent: MS-bar
# for u/d/s/c/b, direct measurements for t). Neutrino masses are known to be
# nonzero but only bounded; the Standard Model itself treats them as massless.
PARTICLES = [
    ("Up quark", "u", "0,0", "+2/3", "1/2", QUARK_COLOR, "≈2.2 MeV/c²", False),
    ("Charm quark", "c", "0,1", "+2/3", "1/2", QUARK_COLOR, "≈1.27 GeV/c²", False),
    ("Top quark", "t", "0,2", "+2/3", "1/2", QUARK_COLOR, "≈172.6 GeV/c²", False),
    ("Down quark", "d", "1,0", "−1/3", "1/2", QUARK_COLOR, "≈4.7 MeV/c²", False),
    ("Strange quark", "s", "1,1", "−1/3", "1/2", QUARK_COLOR, "≈93 MeV/c²", False),
    ("Bottom quark", "b", "1,2", "−1/3", "1/2", QUARK_COLOR, "≈4.18 GeV/c²", False),
    ("Electron", "e", "2,0", "−1", "1/2", NO_COLOR, "≈0.511 MeV/c²", False),
    ("Muon", "μ", "2,1", "−1", "1/2", NO_COLOR, "≈105.7 MeV/c²", False),
    ("Tau", "τ", "2,2", "−1", "1/2", NO_COLOR, "≈1.777 GeV/c²", False),
    ("Electron neutrino", "ν<sub>e</sub>", "3,0", "0", "1/2", NO_COLOR, "< 1 eV/c² (nonzero, exact value unknown)", False),
    ("Muon neutrino", "ν<sub>μ</sub>", "3,1", "0", "1/2", NO_COLOR, "< 1 eV/c² (nonzero, exact value unknown)", False),
    ("Tau neutrino", "ν<sub>τ</sub>", "3,2", "0", "1/2", NO_COLOR, "< 1 eV/c² (nonzero, exact value unknown)", False),
    ("Gluon", "g", "0,3", "0", "1", GLUON_COLOR, "0 (massless)", True),
    ("Photon", "γ", "1,3", "0", "1", NO_COLOR, "0 (massless)", True),
    ("Z boson", "Z<sup>0</sup>", "2,3", "0", "1", NO_COLOR, "≈91.19 GeV/c²", False),
    ("W boson", "W<sup>±</sup>", "3,3", "±1", "1", NO_COLOR, "≈80.37 GeV/c²", False),
    ("Higgs boson", "H", "0,4", "0", "0", NO_COLOR, "≈125.2 GeV/c²", False),
]

# (group label = the answer on the "name the highlighted group" card,
#  question for the "find the group" card, member particle names).
# A group also gets a "name the highlighted group" card when it has at least
# two members, isn't every particle (a single highlighted particle would be
# answered with the particle's name, and "all of them" has no single answer),
# and highlights a different set from every earlier group (so that card has
# one answer).
POS = {p[0]: p[2] for p in PARTICLES}
QUARKS = ["Up quark", "Charm quark", "Top quark", "Down quark", "Strange quark", "Bottom quark"]
CHARGED_LEPTONS = ["Electron", "Muon", "Tau"]
NEUTRINOS = ["Electron neutrino", "Muon neutrino", "Tau neutrino"]
LEPTONS = CHARGED_LEPTONS + NEUTRINOS
FERMIONS = QUARKS + LEPTONS
GAUGE_BOSONS = ["Gluon", "Photon", "Z boson", "W boson"]
BOSONS = GAUGE_BOSONS + ["Higgs boson"]
ALL = FERMIONS + BOSONS

# Which particles each force acts on directly (they carry that force's charge):
#   strong          - color charge: quarks and gluons.
#   electromagnetic - electric charge: quarks, charged leptons, W. (The photon
#                     is neutral: photons don't interact with each other.)
#   weak            - weak isospin/hypercharge: every fermion, plus the W, Z
#                     and Higgs. Gluons and photons are the only exceptions.
#   gravity         - everything with energy, so every particle.
STRONG = QUARKS + ["Gluon"]
ELECTROMAGNETIC = QUARKS + CHARGED_LEPTONS + ["W boson"]
WEAK = FERMIONS + ["W boson", "Z boson", "Higgs boson"]


GROUPS = [
    ("Fermions", "Where are the fermions?", FERMIONS),
    ("Bosons", "Where are the bosons?", BOSONS),
    ("Quarks", "Where are the quarks?", QUARKS),
    ("Leptons", "Where are the leptons?", LEPTONS),
    ("Charged leptons", "Where are the charged leptons?", CHARGED_LEPTONS),
    ("Neutrinos", "Where are the neutrinos?", NEUTRINOS),
    ("Gauge bosons", "Where are the gauge bosons?", GAUGE_BOSONS),
    ("Scalar bosons", "Where are the scalar bosons?", ["Higgs boson"]),
    ("Feel the strong force", "Which particles feel the strong force?", STRONG),
    ("Feel the electromagnetic force", "Which particles feel the electromagnetic force?", ELECTROMAGNETIC),
    ("Feel the weak force", "Which particles feel the weak force?", WEAK),
    ("Feel gravity", "Which particles feel gravity?", ALL),
    # Shared properties. Sets that repeat a group above (e.g. spin 1/2 =
    # fermions) only get the "find" card; see main().
    ("Electric charge +2/3", "Which particles have electric charge +2/3?", ["Up quark", "Charm quark", "Top quark"]),
    ("Electric charge −1/3", "Which particles have electric charge −1/3?", ["Down quark", "Strange quark", "Bottom quark"]),
    ("Electric charge −1", "Which particles have electric charge −1?", CHARGED_LEPTONS),
    ("Electric charge ±1", "Which particles have electric charge ±1?", ["W boson"]),
    ("Electrically neutral", "Which particles are electrically neutral?",
     NEUTRINOS + ["Gluon", "Photon", "Z boson", "Higgs boson"]),
    ("Spin 1/2", "Which particles have spin 1/2?", FERMIONS),
    ("Spin 1", "Which particles have spin 1?", GAUGE_BOSONS),
    ("Spin 0", "Which particles have spin 0?", ["Higgs boson"]),
    ("Carry color charge", "Which particles carry color charge?", STRONG),
    # Mass bands: each is about three orders of magnitude above the last.
    ("Massless", "Which particles are massless?", ["Gluon", "Photon"]),
    ("Mass < 1 eV/c²", "Which particles have a mass under 1 eV/c²?", NEUTRINOS),
    ("Mass 0.5–5 MeV/c²", "Which particles have a mass of 0.5–5 MeV/c²?", ["Electron", "Up quark", "Down quark"]),
    ("Mass 90–110 MeV/c²", "Which particles have a mass of 90–110 MeV/c²?", ["Strange quark", "Muon"]),
    ("Mass 1–5 GeV/c²", "Which particles have a mass of 1–5 GeV/c²?", ["Charm quark", "Tau", "Bottom quark"]),
    ("Mass 80–175 GeV/c²", "Which particles have a mass of 80–175 GeV/c²?",
     ["W boson", "Z boson", "Higgs boson", "Top quark"]),
]


def bar(x):
    """Antiparticle: overlined symbol."""
    return f'<span class="bar">{x}</span>'


NU_E, NU_MU, NU_TAU = "ν<sub>e</sub>", "ν<sub>μ</sub>", "ν<sub>τ</sub>"

# Decays, for each unstable particle: (particle name, its decay products,
# channel lines shown on the back). Stable particles are in STABLE below; every
# particle is in exactly one of the two, and each gets a Decay Products card.
# A fermion's products are the first weak vertex - its weak partner plus a W,
# virtual (*) when the W is heavier than the energy available; the channel
# lines say what that W* turns into. Boson decays list two-body final states.
# Branching fractions: PDG 2024, rounded; minor modes left off the grid.
DECAYS = [
    ("Muon", ["Muon neutrino", "W boson"], [
        f"μ<sup>−</sup> → {NU_MU} W<sup>−</sup>*",
        f"W<sup>−</sup>* → e<sup>−</sup> {bar(NU_E)} (≈100%)",
    ]),
    ("Tau", ["Tau neutrino", "W boson"], [
        f"τ<sup>−</sup> → {NU_TAU} W<sup>−</sup>*",
        f"W<sup>−</sup>* → d {bar('u')} (hadrons, ≈65%)",
        f"W<sup>−</sup>* → e<sup>−</sup> {bar(NU_E)} (≈18%)",
        f"W<sup>−</sup>* → μ<sup>−</sup> {bar(NU_MU)} (≈17%)",
    ]),
    ("Top quark", ["Bottom quark", "W boson"], [
        "t → b W<sup>+</sup> (≈100%, a real W)",
    ]),
    ("Bottom quark", ["Charm quark", "W boson"], [
        "b → c W<sup>−</sup>* (≈98%; b → u is CKM-suppressed)",
    ]),
    ("Charm quark", ["Strange quark", "W boson"], [
        "c → s W<sup>+</sup>* (≈95%; c → d is CKM-suppressed)",
    ]),
    ("Strange quark", ["Up quark", "W boson"], [
        "s → u W<sup>−</sup>* (inside kaons and hyperons)",
    ]),
    ("Down quark", ["Up quark", "W boson"], [
        "d → u W<sup>−</sup>*",
        f"W<sup>−</sup>* → e<sup>−</sup> {bar(NU_E)} (neutron beta decay)",
    ]),
    ("W boson", ["Up quark", "Down quark", "Charm quark", "Strange quark"] + LEPTONS, [
        f"W<sup>+</sup> → quark pair (≈67%: mainly u {bar('d')}, c {bar('s')})",
        f"W<sup>+</sup> → e<sup>+</sup> {NU_E}, μ<sup>+</sup> {NU_MU}, τ<sup>+</sup> {NU_TAU} (≈11% each)",
    ]),
    ("Z boson", [q for q in QUARKS if q != "Top quark"] + LEPTONS, [
        f"Z → q {bar('q')} (≈70%: any quark but t, which is too heavy)",
        f"Z → ν {bar('ν')} (≈20%, all three flavors)",
        "Z → e<sup>+</sup>e<sup>−</sup>, μ<sup>+</sup>μ<sup>−</sup>, τ<sup>+</sup>τ<sup>−</sup> (≈3.4% each)",
    ]),
    ("Higgs boson", ["Bottom quark", "W boson", "Gluon", "Tau", "Charm quark", "Z boson", "Photon"], [
        f"H → b {bar('b')} (≈58%)",
        "H → W W* (≈21%)",
        "H → g g (≈8%, via a top-quark loop)",
        "H → τ<sup>+</sup>τ<sup>−</sup> (≈6%)",
        f"H → c {bar('c')} (≈3%)",
        "H → Z Z* (≈3%)",
        "H → γγ (≈0.2%), Zγ (≈0.15%), via loops",
    ]),
]


# Particles that don't decay: (name, reason shown under "Does not decay").
STABLE = [
    ("Up quark", "The lightest quark: there is nothing lighter for it to turn into."),
    ("Electron", "The lightest charged particle, so charge conservation forbids it."),
    ("Electron neutrino", "Neutrinos oscillate between flavors, but they don't decay."),
    ("Muon neutrino", "Neutrinos oscillate between flavors, but they don't decay."),
    ("Tau neutrino", "Neutrinos oscillate between flavors, but they don't decay."),
    ("Photon", "Massless, so it has no energy at rest to decay with."),
    ("Gluon", "Massless, so it has no energy at rest to decay with (and it is confined inside hadrons)."),
]


def decay_fields():
    """name -> (Products positions, Channels HTML) for every particle."""
    names = [p[0] for p in PARTICLES]
    out = {}
    for name, products, channels in DECAYS:
        assert len(set(products)) == len(products) and name not in products, name
        out[name] = (" ".join(POS[p] for p in products), "<br>".join(channels))
    for name, reason in STABLE:
        assert name not in out, f"{name} is in both DECAYS and STABLE"
        out[name] = ("", f"Does not decay<br>{reason}")
    assert sorted(out) == sorted(names), f"missing: {set(names) - set(out)}"
    return out


def identify_signatures():
    """Property-set text for particles uniquely identified by (charge, spin, color charge, massless?)."""
    def key(p):
        return (p[3], p[4], p[5], p[7])
    counts = {}
    for p in PARTICLES:
        counts[key(p)] = counts.get(key(p), 0) + 1
    out = {}
    for p in PARTICLES:
        if counts[key(p)] == 1:
            out[p[0]] = "<br>".join([
                f"Electric charge: {p[3]}",
                f"Spin: {p[4]}",
                f"Color charge: {p[5]}",
                "Massless" if p[7] else "Massive",
            ])
    return out


def write(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main():
    os.makedirs(DECK, exist_ok=True)
    sigs = identify_signatures()
    decays = decay_fields()
    write(
        os.path.join(DECK, "Particle.tsv"),
        ("Name", "Symbol", "Position", "Charge", "Spin", "Color Charge", "Mass", "Identify",
         "Products", "Channels", "Tags"),
        [(n, sym, pos, q, s, col, m, sigs.get(n, ""), *decays[n], "")
         for n, sym, pos, q, s, col, m, _ in PARTICLES],
    )
    rows = []
    seen_sets = {}
    for group, question, members in GROUPS:
        assert len(set(members)) == len(members), f"{group!r} lists a particle twice"
        key = frozenset(members)
        repeat = key in seen_sets
        seen_sets.setdefault(key, group)
        positions = " ".join(POS[m] for m in members)
        ask_set = "yes" if 2 <= len(members) < len(ALL) and not repeat else ""
        rows.append((group, question, positions, ask_set, ""))
    write(os.path.join(DECK, "Group.tsv"), ("Group", "Question", "Members", "Ask Set", "Tags"), rows)
    print(f"wrote {len(PARTICLES)} particles ({len(sigs)} with property-set cards: "
          f"{', '.join(sigs)}), {len(GROUPS)} groups; {len(DECAYS)} decay, {len(STABLE)} stable")


if __name__ == "__main__":
    main()
