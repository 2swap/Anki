"""Generate Mineral.tsv and manifest.json's "media" map.

Each mineral is (name, formula, crystal system, class, [up to 6 facts]); fact i
fills the "Fact i" field and gets its own Fact-to-Name card. Formulas are
written plainly ("CaSO4·2H2O"); digits right after an element or ")" become
subscripts. Complex rock-forming silicates use their usual simplified formula.
Images come from fetch_images.py (network, run by hand); a mineral without a
downloaded image gets no card (the back needs one).

Run by anki_sync.py check/push (manifest.json's "build" key), or standalone.
"""

import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Mineral.tsv")
MANIFEST = os.path.join(HERE, "manifest.json")

MINERALS = [
    # The Mohs scale
    ("Talc", "Mg3Si4O10(OH)2", "Triclinic", "Silicate (sheet)", [
      "Mohs hardness reference mineral 1: the softest mineral",
      "Ground into talcum powder",
      "Main mineral of soapstone, a soft carving stone that feels soapy",
      "Magnesium sheet silicate used as a filler in ceramics and paper",
    ]),
    ("Gypsum", "CaSO4·2H2O", "Monoclinic", "Sulfate", [
      "Mohs hardness reference mineral 2: scratched by a fingernail",
      "Used to make plaster and drywall",
      "Selenite and desert rose are varieties of it",
      "Hydrated calcium sulfate whose thick beds mark ancient evaporated seas",
      "Most modern blackboard chalk is made of it",
    ]),
    ("Calcite", "CaCO3", "Trigonal", "Carbonate", [
      "Mohs hardness reference mineral 3",
      "The classic mineral that fizzes strongly in cold dilute acid",
      "Clear crystals (Iceland spar) show double refraction, which was key to early optics",
      "Main mineral of limestone and marble, among Earth's largest carbon stores",
      "Heated to make lime and cement",
    ]),
    ("Fluorite", "CaF2", "Cubic", "Halide", [
      "Mohs hardness reference mineral 4",
      "Often forms purple or green cubes",
      "Many samples glow under UV light, and the word \"fluorescence\" comes from it",
      "The element fluorine is named after it",
      "Main source of fluorine for hydrofluoric acid, Teflon and refrigerants",
      "Calcium halide used as a flux in steelmaking (its name comes from Latin for \"to flow\")",
    ]),
    ("Apatite", "Ca5(PO4)3F", "Hexagonal", "Phosphate", [
      "Mohs hardness reference mineral 5",
      "The mineral that makes up teeth and bones",
      "Main source of phosphate fertilizer, which has no substitute in farming",
    ]),
    ("Orthoclase", "KAlSi3O8", "Monoclinic", "Silicate (framework)", [
      "Mohs hardness reference mineral 6",
      "Pink potassium feldspar that gives granite its pink color",
      "Monoclinic, higher-temperature form of potassium feldspar (KAlSi3O8)",
    ]),
    ("Quartz", "SiO2", "Trigonal", "Silicate (framework)", [
      "Mohs hardness reference mineral 7: scratches glass",
      "Amethyst, citrine and rose quartz are varieties of it",
      "Second most common mineral in Earth's crust and the main grain in sand",
      "Raw material for glass and silicon chips",
      "Piezoelectric crystals of it keep time in watches and electronics",
    ]),
    ("Topaz", "Al2SiO4(F,OH)2", "Orthorhombic", "Silicate (isolated)", [
      "Mohs hardness reference mineral 8",
      "Gemstone that is colorless when pure, often blue (usually from treatment) or golden",
      "Fluorine-bearing aluminum silicate gem that marks fluorine-rich granites and pegmatites, often with tin and tungsten",
    ]),
    ("Corundum", "Al2O3", "Trigonal", "Oxide", [
      "Mohs hardness reference mineral 9",
      "Its red gem variety is ruby",
      "Every gem color of it except red is called sapphire",
      "Aluminum oxide used as an abrasive (emery)",
      "Grown synthetically as \"sapphire glass\" for watch faces and phone camera covers",
      "The first laser (1960) used a crystal of its red variety",
    ]),
    ("Diamond", "C", "Cubic", "Native element", [
      "Mohs hardness reference mineral 10: the hardest natural mineral",
      "Carbon mineral that forms deep in the mantle; same element as graphite in a different structure",
      "Best natural conductor of heat",
      "The hardest material, used to tip cutting and drilling tools",
      "Its crystals and their inclusions are samples brought up from the deep mantle",
    ]),

    # Native elements
    ("Graphite", "C", "Hexagonal", "Native element", [
      "Same element as diamond, but in sheets that slide over each other, so it is very soft",
      "Pencil \"lead\"",
      "The anode in every lithium-ion battery",
      "Carbon mineral used as a dry lubricant and for steelmaking electrodes",
      "A single layer of it is graphene",
    ]),
    ("Gold", "Au", "Cubic", "Native element", [
      "Very dense, soft native metal that never tarnishes",
      "The native metal that has stored monetary value through human history",
      "Plated onto electronic contacts because it never corrodes",
    ]),
    ("Silver", "Ag", "Cubic", "Native element", [
      "Native metal that often forms wiry growths",
      "Native metal that tarnishes black",
      "The best electrical and heat conductor of all metals",
      "Native metal used for coins, film photography, and now solar panels",
    ]),
    ("Copper", "Cu", "Cubic", "Native element", [
      "Native metal that tarnishes brown to green, often in branching (dendritic) masses",
      "Probably the first metal humans worked",
      "The metal that carries electricity in nearly all wiring",
    ]),
    ("Sulfur", "S", "Orthorhombic", "Native element", [
      "Bright yellow native element that forms around volcanic vents",
      "Raw material for sulfuric acid, the most produced industrial chemical",
      "Yellow native element used in gunpowder and to vulcanize rubber",
    ]),

    # Sulfides
    ("Pyrite", "FeS2", "Cubic", "Sulfide", [
      "\"Fool's gold\": brassy cubes, harder and more brittle than gold",
      "The most common sulfide mineral",
      "Iron sulfide whose weathering causes acid mine drainage",
      "Cubic iron sulfide once roasted to make sulfuric acid",
    ]),
    ("Marcasite", "FeS2", "Orthorhombic", "Sulfide", [
      "Same formula as pyrite in a different (orthorhombic) structure; paler",
      "Iron sulfide that crumbles over time (\"pyrite decay\"), damaging museum specimens",
    ]),
    ("Galena", "PbS", "Cubic", "Sulfide", [
      "Main ore of lead",
      "Heavy, silvery cubes that break into smaller cubes",
      "Lead sulfide that is also a major source of silver",
      "Early crystal radios used it as the detector (\"cat's whisker\")",
    ]),
    ("Sphalerite", "ZnS", "Cubic", "Sulfide", [
      "Main ore of zinc",
      "Zinc sulfide, usually brown to black with a resinous shine",
      "Byproduct source of germanium, gallium and indium for electronics",
    ]),
    ("Chalcopyrite", "CuFeS2", "Tetragonal", "Sulfide", [
      "The world's most important copper ore",
      "Brassy yellow copper-iron sulfide, often with an iridescent tarnish",
    ]),
    ("Cinnabar", "HgS", "Trigonal", "Sulfide", [
      "Main ore of mercury",
      "Bright red, toxic mercury sulfide",
      "Ground to make vermilion, a red pigment used since ancient times",
    ]),
    ("Molybdenite", "MoS2", "Hexagonal", "Sulfide", [
      "Soft, silvery flakes that look like graphite but are a sulfide",
      "Main ore of molybdenum, which strengthens steel",
      "Sulfide whose rhenium content allows rhenium-osmium (Re-Os) dating",
      "A single layer of it is a 2D semiconductor, a counterpart to graphene",
    ]),
    ("Stibnite", "Sb2S3", "Orthorhombic", "Sulfide", [
      "Long, metallic, needle-like crystals of a sulfide",
      "Main ore of antimony, a critical mineral used in flame retardants, batteries and ammunition",
      "Ground to make the ancient eyeliner kohl",
    ]),

    # Halides
    ("Halite", "NaCl", "Cubic", "Halide", [
      "Rock salt: tastes salty and forms cubes",
      "Spread on roads to melt ice",
      "Starting point of the chlorine and lye (chlor-alkali) industry",
      "Forms underground domes that trap oil and are used to store fuel and waste",
    ]),
    ("Sylvite", "KCl", "Cubic", "Halide", [
      "Looks like halite but tastes more bitter",
      "Major source of potash, supplying the K in N-P-K fertilizer",
    ]),

    # Oxides and hydroxides
    ("Hematite", "Fe2O3", "Trigonal", "Oxide", [
      "Main ore of iron, and so the basis of steel",
      "Can look black and metallic, but always leaves a red-brown streak",
      "Iron oxide in banded iron formations that record the rise of oxygen in the atmosphere",
      "Makes Mars and many red rocks red",
      "Ground into red ochre, humanity's first pigment",
    ]),
    ("Magnetite", "Fe3O4", "Cubic", "Oxide", [
      "The most strongly magnetic natural mineral",
      "Lodestone, which made the first compasses, is a naturally magnetized form of it",
      "Iron oxide whose grains record past magnetic fields in rocks, key evidence for plate tectonics",
    ]),
    ("Ilmenite", "FeTiO3", "Trigonal", "Oxide", [
      "Black, weakly magnetic main ore of titanium",
      "Main source of titanium dioxide, the white pigment in paint, paper, plastics and sunscreen",
    ]),
    ("Chromite", "FeCr2O4", "Cubic", "Oxide", [
      "The only ore of chromium",
      "The ore of the metal that makes stainless steel stainless",
    ]),
    ("Spinel", "MgAl2O4", "Cubic", "Oxide", [
      "Its red variety was long mistaken for ruby",
      "The Black Prince's Ruby in the British crown is actually this mineral",
      "Magnesium aluminum oxide that names a crystal structure found in the mantle and in battery cathodes",
    ]),
    ("Cassiterite", "SnO2", "Tetragonal", "Oxide", [
      "Main ore of tin; heavy and usually brown to black",
      "The ore whose tin made bronze, and so the Bronze Age, possible",
      "Tin oxide ore listed as a conflict mineral; its tin goes into electronics solder",
    ]),
    ("Goethite", "FeO(OH)", "Orthorhombic", "Oxide (hydroxide)", [
      "Iron hydroxide that is a major part of rust",
      "Main coloring mineral of yellow-brown ochre",
      "Gives soils and tropical laterites their yellow-brown color",
      "Iron hydroxide found on Mars as evidence of past water",
    ]),

    # Carbonates
    ("Aragonite", "CaCO3", "Orthorhombic", "Carbonate", [
      "Same formula as calcite in a different (orthorhombic) structure",
      "Makes up corals, pearls and many shells",
      "The carbonate mineral at the center of concerns about ocean acidification",
    ]),
    ("Dolomite", "CaMg(CO3)2", "Trigonal", "Carbonate", [
      "Like calcite, but fizzes only weakly in acid unless powdered",
      "Gives its name to a mountain range in the Italian Alps",
      "Calcium magnesium carbonate whose rare formation today is a long-standing geological puzzle",
    ]),
    ("Siderite", "FeCO3", "Trigonal", "Carbonate", [
      "Brown iron carbonate; an iron ore",
      "Iron carbonate that forms only in low-oxygen conditions, a clue to early Earth and Mars",
    ]),
    ("Rhodochrosite", "MnCO3", "Trigonal", "Carbonate", [
      "Pink to red carbonate, often banded",
      "Manganese carbonate ore prized as a collector's and gem mineral",
    ]),
    ("Azurite", "Cu3(CO3)2(OH)2", "Monoclinic", "Carbonate", [
      "Deep blue copper carbonate, often found with malachite and slowly turning into it",
      "Blue pigment of medieval and Renaissance paintings",
      "Its blue stains on rock point prospectors to copper deposits",
    ]),

    # Sulfates
    ("Barite", "BaSO4", "Orthorhombic", "Sulfate", [
      "Unusually heavy for a light-colored mineral; often bladed crystals",
      "Mostly used to weight oil-well drilling mud",
      "Barium sulfate given as a \"barium meal\" for X-ray imaging",
    ]),
    ("Anhydrite", "CaSO4", "Orthorhombic", "Sulfate", [
      "Gypsum without the water; turns into gypsum when it absorbs water",
      "Calcium sulfate that swells as it turns to gypsum, damaging tunnels and foundations",
    ]),

    # Silicates
    ("Olivine", "(Mg,Fe)2SiO4", "Orthorhombic", "Silicate (isolated)", [
      "Olive-green mineral common in basalt",
      "Main mineral of the upper mantle, probably the most abundant mineral in Earth's upper layers",
      "Its gem form is peridot",
      "Green magnesium-iron silicate that weathers quickly and is studied for capturing CO2",
    ]),
    ("Garnet", "Fe3Al2(SiO4)3", "Cubic", "Silicate (isolated)", [
      "Red-brown mineral group common in metamorphic rocks; almandine is the common one",
      "Mineral group petrologists use to work out the pressure and temperature a metamorphic rock went through",
      "Mineral group used as an abrasive for waterjet cutting and sandpaper",
      "The January birthstone",
    ]),
    ("Zircon", "ZrSiO4", "Tetragonal", "Silicate (isolated)", [
      "Durable mineral that keeps its uranium-lead clock, so it is the main mineral for dating rocks",
      "Grains of it over 4.4 billion years old are the oldest known pieces of Earth and show early Earth had water",
      "Ore of zirconium, used in nuclear reactor fuel cladding",
    ]),
    ("Beryl", "Be3Al2Si6O18", "Hexagonal", "Silicate (ring)", [
      "Its green variety is emerald",
      "Its blue-green variety is aquamarine",
      "Main ore of beryllium, used in aerospace alloys and X-ray windows",
    ]),
    ("Tourmaline", "NaFe3Al6(BO3)3Si6O18(OH)4", "Trigonal", "Silicate (ring)", [
      "Long, striated prisms; the common variety (schorl) is black",
      "Gem mineral group in many colors, including pink-and-green \"watermelon\" slices",
      "Gem silicate that is pyroelectric and piezoelectric: heating or squeezing it builds up charge",
      "The main mineral that holds boron in rocks",
    ]),
    ("Hornblende", "Ca2(Mg,Fe,Al)5(Al,Si)8O22(OH)2", "Monoclinic", "Silicate (double chain)", [
      "The most common amphibole; dark, elongated crystals common in granite and diorite",
      "Amphibole whose aluminum content is used to estimate the pressure at which igneous rocks crystallized",
    ]),
    ("Muscovite", "KAl2(AlSi3O10)(OH)2", "Monoclinic", "Silicate (sheet)", [
      "Clear to silvery mica that peels into thin, flexible sheets",
      "Mica used for stove windows (\"isinglass\") and electrical insulation",
      "Light-colored mica whose potassium is used for argon-argon dating",
    ]),
    ("Kaolinite", "Al2Si2O5(OH)4", "Triclinic", "Silicate (sheet)", [
      "White clay mineral used in porcelain (\"china clay\")",
      "Clay mineral that forms when feldspar weathers",
      "White clay that coats glossy paper and gave its name to the medicine Kaopectate",
    ]),
    ("Serpentine", "Mg3Si2O5(OH)4", "Monoclinic", "Silicate (sheet)", [
      "Group of green minerals that form when olivine reacts with water",
      "Its fibrous form (chrysotile) is a type of asbestos",
      "Its formation at seafloor vents releases hydrogen and methane, possibly where life began",
      "Hydrated mineral group that carries water down into subduction zones",
    ]),
    ("Microcline", "KAlSi3O8", "Triclinic", "Silicate (framework)", [
      "Same formula as orthoclase, but triclinic",
      "Its green variety is amazonite",
      "Low-temperature potassium feldspar that often forms giant crystals in pegmatites",
    ]),
]


def media_name(name):
    return "mineral_" + re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") + ".jpg"


def formula_html(formula):
    html = re.sub(r"(?<=[A-Za-z)])(\d+)", r"<sub>\1</sub>", formula)
    # Let long formulas wrap on a phone, after a group's subscript
    return re.sub(r"(\)(?:<sub>\d+</sub>)?)(?!<sub>)(?=.)", r"\1<wbr>", html)


def main():
    names = [m[0] for m in MINERALS]
    assert len(set(names)) == len(names), "duplicate mineral name"
    rows, media = [], {}
    for name, formula, system, cls, facts in MINERALS:
        assert 1 <= len(facts) <= 6, f"{name}: {len(facts)} facts"
        img = media_name(name)
        image = ""
        if os.path.exists(os.path.join(HERE, "media", img)):
            image = f'<img src="{img}">'
            media[img] = f"media/{img}"
        rows.append([name, image, formula_html(formula), system, cls, *facts, *[""] * (6 - len(facts)), ""])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["Name", "Image", "Formula", "Crystal System", "Class",
                         *[f"Fact {i}" for i in range(1, 7)], "Tags"])
        writer.writerows(rows)
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["media"] = media
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {len(rows)} minerals ({len(media)} with images) to {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
