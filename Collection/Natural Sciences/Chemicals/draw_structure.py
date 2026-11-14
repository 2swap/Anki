"""Draw a molecule's structure SVG in the same style as the rest of this deck.

    python3 draw_structure.py "Caffeine" "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

writes media/chem_caffeine.svg and prints the TSV row (Name, Formula, SMILES,
Structure) to append to Chemical.tsv. Also add the file to
manifest.json's "media" map. Formula uses <sub> for digits; check it by hand
for ions and hydrates.

The deck's images were made with RDKit's MolDraw2DSVG at 360x260, padding
0.08, transparent background, default 2D layout. These settings reproduce 90
of the existing 127 SVGs byte for byte (once the stroke-miterlimit newer RDKit
adds is dropped) and the rest nearly so, differing only in which ring bonds
are drawn double or a slight rotation.
"""
import os
import re
import sys

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

HERE = os.path.dirname(os.path.abspath(__file__))


def slug(name):
    """'Sodium chloride (table salt)' -> chem_sodium_chloride.svg"""
    base = re.sub(r"\s*\([^()]*\)\s*$", "", name)
    return "chem_" + re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") + ".svg"


def draw(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise SystemExit(f"RDKit can't parse SMILES {smiles!r}")
    d = rdMolDraw2D.MolDraw2DSVG(360, 260)
    opts = d.drawOptions()
    opts.clearBackground = False
    opts.padding = 0.08
    d.DrawMolecule(rdMolDraw2D.PrepareMolForDrawing(mol))
    d.FinishDrawing()
    return mol, d.GetDrawingText().replace("stroke-miterlimit:10;", "")


def main(name, smiles):
    mol, svg = draw(smiles)
    fname = slug(name)
    with open(os.path.join(HERE, "media", fname), "w", encoding="iso-8859-1") as fh:
        fh.write(svg)
    formula = re.sub(r"(?<=[A-Za-z)])(\d+)", r"<sub>\1</sub>", CalcMolFormula(mol))
    print(f"wrote media/{fname}")
    print("\t".join([name, formula, smiles, f'<img src="{fname}">', "chemicals"]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
