"""One-shot: replace vernacular node names in tree_of_life.json with the
clade names used in the literature, drop paraphyletic form-taxa that have no
clade equivalent, and expand a few where the split is clean and contained.

Also rewrites the AUTHORED / _ADJUST / TAG_ROOTS keys in build_clade_tsv.py.
Kept in the repo as a record; safe to re-run (idempotent once applied).

Run from anywhere:  python "Life/refactor_names.py"
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.join(HERE, "shared_media", "tree_of_life.json")
BUILD = os.path.join(HERE, "build_clade_tsv.py")

# vernacular / informal -> literature clade name (same clade, no restructure)
RENAME = {
    "Mammals": "Mammalia",
    "Amphibians": "Lissamphibia",
    "Lampreys": "Petromyzontiformes",
    "Hagfishes": "Myxiniformes",
    "Crocodiles": "Crocodylia",
    "Platypus": "Ornithorhynchidae",
    "Echidnas": "Tachyglossidae",
    "Rodents": "Rodentia",
    "Lagomorphs": "Lagomorpha",
    "Lemurs": "Lemuriformes",
    "Lorises": "Lorisiformes",
    "Tarsiers": "Tarsiiformes",
    "Capuchins": "Cebinae",
    "Squirrel Monkeys": "Saimiriinae",
    "Howler Monkeys": "Alouattinae",
    "Spider Monkeys": "Atelinae",
    "Titis": "Callicebinae",
    "Chimpanzees": "Pan troglodytes",
    "Bonobos": "Pan paniscus",
    "Ungulates": "Euungulata",
    "Canoidea": "Caniformia",
    "Feloidea": "Feliformia",
    "Lancelets": "Cephalochordata",
    "Tunicates": "Tunicata",
    "Earthworms": "Crassiclitellata",
    "Leeches": "Hirudinea",
    "Centipedes": "Chilopoda",
    "Millipedes": "Diplopoda",
    "Horseshoe Crabs": "Xiphosura",
    "Arachnids": "Arachnida",
    "Scorpions": "Scorpiones",
    "Crustaceans": "Crustacea",
    "Cephalopods": "Cephalopoda",
    "Octopuses": "Octopodiformes",
    "Squids": "Decapodiformes",
    "Ferns": "Polypodiopsida",
    "Polypodiopsida": "Polypodiidae",
    "Equisetopsida": "Equisetidae",
    "Marattiopsida": "Marattiidae",
    "Psilotopsida": "Ophioglossidae",
    "Grasses": "Poaceae",
    "Lilies": "Liliales",
    "Orchids": "Orchidaceae",
    "Conifers": "Pinophyta",
    "Cycads": "Cycadophyta",
    "Ginkgo": "Ginkgophyta",
    "Gnetophytes": "Gnetophyta",
    "Mosses": "Bryopsida",
    "Liverworts": "Marchantiophyta",
    "Hornworts": "Anthocerotophyta",
    "Gymnosperms": "Acrogymnospermae",
    "Streptophyte Algae": "Charophyta",
}

# paraphyletic / polyphyletic form-taxa with no clade equivalent -> removed
DROP = {
    "Snails", "Slugs", "Clams", "Oysters", "Frogs", "Toads",
    "Lizards", "Snakes", "Turtles", "Tortoises",
    "Marmosets", "Tamarins", "Sakis", "Uakaris", "Fissipedia",
}
# Fissipedia has children; move them up before deleting it.
REPARENT_ON_DROP = {"Fissipedia": "Carnivora"}

# new nodes (name, parent) -- parents named post-rename
ADD = [
    ("Pleurodira", "Testudines"),
    ("Cryptodira", "Testudines"),
    ("Rhynchocephalia", "Lepidosauria"),
    ("Squamata", "Lepidosauria"),
    ("Coleoidea", "Cephalopoda"),
    ("Nautiloidea", "Cephalopoda"),
    ("Pitheciinae", "Pitheciidae"),
    ("Canidae", "Caniformia"),
    ("Arctoidea", "Caniformia"),
    ("Ursidae", "Arctoidea"),
    ("Musteloidea", "Arctoidea"),
]
REPARENT = {
    "Octopodiformes": "Coleoidea",
    "Decapodiformes": "Coleoidea",
    "Pinnipedia": "Arctoidea",
}


def transform_tree():
    with open(TREE, encoding="utf-8") as fh:
        old = json.load(fh)

    order = list(old)  # preserve order
    new = {}
    for name in order:
        if name in DROP:
            continue
        nn = RENAME.get(name, name)
        p = old[name]["parent"]
        if p in REPARENT_ON_DROP:
            p = REPARENT_ON_DROP[p]
        p = RENAME.get(p, p) if p else None
        assert nn not in new, f"name collision on {nn}"
        new[nn] = {"parent": p}

    for name, parent in ADD:
        assert name not in new, name
        new[name] = {"parent": parent}
    for child, parent in REPARENT.items():
        new[child]["parent"] = parent

    # validate
    for k, v in new.items():
        assert v["parent"] is None or v["parent"] in new, f"dangling parent: {k} -> {v['parent']}"
    seen, stack = set(), ["Life"]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack += [k for k, v in new.items() if v["parent"] == n]
    assert set(new) == seen, f"unreachable: {set(new) - seen}"

    # write in the original compact one-line-per-node style, original order first
    lines = ["{"]
    emitted = list(new)
    for i, name in enumerate(emitted):
        p = new[name]["parent"]
        pval = "null" if p is None else json.dumps(p)
        comma = "" if i == len(emitted) - 1 else ","
        lines.append(f'  {json.dumps(name)}: {{ "parent": {pval} }}{comma}')
    lines.append("}")
    with open(TREE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"tree_of_life.json: {len(old)} -> {len(new)} nodes")


def rewrite_build_keys():
    with open(BUILD, encoding="utf-8") as fh:
        src = fh.read()

    def repl(m):
        indent, key, rest = m.group(1), m.group(2), m.group(3)
        return f'{indent}{json.dumps(RENAME.get(key, key))}{rest}'

    # AUTHORED / _ADJUST / TAG_ROOTS entries all start a line as  "Key": ( / "Key": "..."
    src = re.sub(r'^(\s+)"([^"]+)"(\s*:\s*[\(\"])', repl, src, flags=re.M)
    with open(BUILD, "w", encoding="utf-8") as fh:
        fh.write(src)
    print("build_clade_tsv.py: AUTHORED/_ADJUST/TAG_ROOTS keys renamed")


if __name__ == "__main__":
    transform_tree()
    rewrite_build_keys()
    print("\nDROPPED:", ", ".join(sorted(DROP)))
    print("ADDED:  ", ", ".join(n for n, _ in ADD))
