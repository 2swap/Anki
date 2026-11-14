"""Regenerate Decks/Life/Clade.tsv for the "Life - Clade" note type.

One note per node in shared_media/tree_of_life.json (the whole tree of life).
`Parent` and `Children` are derived from that topology. `Traits`,
`DivergenceMya` and `GeoTime` are authored per-clade in AUTHORED below; clades
absent from AUTHORED get blank values, so their Divergence-Time and
Identify-from-Traits cards simply aren't generated yet.

Divergence-time convention: DivergenceMya is the approximate age of the clade's
crown node -- i.e. when its own lineages first diverged from one another. Figures
are round textbook estimates (Prum et al. 2015 / Claramunt & Cracraft 2015 and
similar); the Paleocene bird radiation is genuinely uncertain by +/- 10 Myr, so
treat them as starting points and adjust.

GeoTime granularity (per project rule):
  - Cenozoic  -> epoch  (Paleocene, Eocene, Oligocene, Miocene, ...)
  - rest of Phanerozoic -> period (Cretaceous, Jurassic, ...) with Early/Late in parens
  - Precambrian -> era

Run from anywhere:  python "Life/build_clade_tsv.py"
"""

import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.join(HERE, "shared_media", "tree_of_life.json")
OUT = os.path.join(HERE, "Decks", "Life", "Clade.tsv")

FIELDS = ["Clade", "Parent", "Children", "Traits", "DivergenceMya", "GeoTime"]

# A node is tagged with the tag of every listed root it descends from (inclusive),
# so cards can be filtered by group. Order doesn't matter.
TAG_ROOTS = {
    "Eukaryota": "eukaryotes",
    "Viridiplantae": "plants",
    "Fungi": "fungi",
    "Metazoa": "animals",
    "Chordata": "chordates",
    "Vertebrata": "vertebrates",
    "Mammalia": "mammals",
    "Aves": "birds",
    "Primates": "primates",
    "Arthropoda": "arthropods",
}

# clade -> (traits, divergence_mya, geo_time). Only clades with authored data;
# every other node in the tree still gets a note, just with these fields blank.
AUTHORED = {
    "Aves": (
        "Toothless keratinous beak; no teeth; short tail ending in a plough-shaped "
        "pygostyle; fused synsacrum; large keeled sternum and furcula; flow-through "
        "air-sac lungs; feathers with an aftershaft.",
        130, "Cretaceous (Early)",
    ),
    "Palaeognathae": (
        "Palaeognathous ('ancient') palate: a rigid, robust bony palate with a large "
        "vomer bracing the pterygoid-palatine complex and prominent basipterygoid "
        "processes.",
        90, "Cretaceous (Late)",
    ),
    "Tinamous": (
        "The only palaeognaths that fly: a fully keeled sternum and functional flight "
        "muscles retained; compact ground-dwelling body, very short tail, cryptic "
        "plumage; males incubate.",
        30, "Oligocene",
    ),
    "Neognathae": (
        "Neognathous ('new') palate: a mobile, kinetic palate with a reduced vomer, "
        "reduced or absent basipterygoid processes and a flexible pterygoid-palatine "
        "joint, allowing cranial kinesis of the upper bill.",
        100, "Cretaceous (Late)",
    ),
    "Galloanserae": (
        "Basal neognaths ('fowl'); precocial, downy, nidifugous chicks; shared derived "
        "features of the skull and pelvis (support is largely molecular).",
        80, "Cretaceous (Late)",
    ),
    "Galliformes": (
        "Short, stout, slightly down-curved bill; heavy body, short rounded wings and "
        "explosive burst flight; strong feet with blunt claws for scratching; large "
        "crop and muscular gizzard; often bare facial skin, combs or wattles.",
        50, "Eocene",
    ),
    "Anseriformes": (
        "Broad flattened bill lined with filtering lamellae; palmate (webbed) feet; "
        "dense waterproof plumage with thick down and an enlarged uropygial gland; "
        "males retain an intromittent phallus.",
        60, "Paleocene",
    ),
    "Neoaves": (
        "~95% of living bird species; a near-instantaneous radiation across the "
        "Cretaceous-Paleogene boundary, so there is no single skeletal synapomorphy "
        "for the whole clade.",
        68, "Cretaceous (Late)",
    ),
    "Strisores": (
        "Aerial insectivores and nectarivores with a tiny bill but very wide gape; "
        "small weak feet and short legs; ancestrally nocturnal/crepuscular; many use "
        "torpor; long pointed wings.",
        62, "Paleocene",
    ),
    "Columbaves": (
        "A landbird assemblage of doves, sandgrouse, mesites, turacos, cuckoos and "
        "bustards; ancestrally granivorous/frugivorous ground and canopy feeders; "
        "clade support is chiefly molecular.",
        60, "Paleocene",
    ),
    "Gruiformes": (
        "Marsh and grassland birds (rails, crakes, cranes, finfoots); laterally "
        "compressed body and long toes for moving through dense vegetation; reduced "
        "tail; frequent evolution of island flightlessness; precocial dark downy chicks.",
        54, "Paleocene",
    ),
    "Aequorlitornithes": (
        "The great water-associated radiation (shorebirds, gulls, plovers, flamingos, "
        "grebes, loons, penguins, tubenoses, herons, pelicans); convergent aquatic "
        "adaptations - supraorbital salt glands, dense waterproof plumage, webbed or "
        "lobed feet - rather than one shared skeletal trait.",
        62, "Paleocene",
    ),
    "Telluraves": (
        "'Core landbirds'; ancestrally arboreal with a raptorial common ancestor "
        "hypothesised (strong grasping feet, hooked bill); altricial, nest-bound young.",
        63, "Paleocene",
    ),
    "Afroaves": (
        "The 'Africa-origin' landbird clade (accipitrids, owls, mousebirds, trogons, "
        "hornbills, rollers, woodpeckers); ancestrally predatory; cavity nesting and "
        "semi-zygodactyl feet are widespread.",
        62, "Paleocene",
    ),
    "Accipitriformes": (
        "Hooked raptorial bill with a fleshy cere; powerful feet with long curved "
        "talons and an enlarged killing hallux; forward-set eyes with acute vision and "
        "a bony brow ridge; broad soaring wings; reversed size dimorphism (females "
        "larger).",
        50, "Eocene",
    ),
    "Strigiformes": (
        "Huge forward-facing eyes locked in sclerotic tubes; a facial disc of stiff "
        "feathers funnelling sound to often asymmetrical ear openings; silent flight "
        "from comb-fringed, velvety flight feathers; reversible outer toe; nocturnal.",
        50, "Eocene",
    ),
    "Coraciiformes": (
        "Syndactyl feet, with the front toes fused along part of their length; large "
        "head on a short neck with a long, often dagger-like bill; nest in burrows or "
        "cavities; naked altricial chicks; frequently iridescent plumage.",
        48, "Eocene",
    ),
    "Piciformes": (
        "Zygodactyl feet (two toes forward, two back); strong chisel- or "
        "shovel-shaped bill; obligate cavity nesters laying white eggs; blind naked "
        "chicks with prominent heel pads. Woodpeckers add a reinforced skull, stiff "
        "prop tail and a very long wrap-around hyoid.",
        50, "Eocene",
    ),
    "Australaves": (
        "The 'southern' core landbirds (seriemas, falcons, parrots, passerines); "
        "ancestrally raptorial; the parrot + passerine subclade shows extreme brain "
        "enlargement and vocal learning.",
        62, "Paleocene",
    ),
    "Falconiformes": (
        "Hooked bill with a pointed 'tomial tooth' notch for severing prey vertebrae "
        "(prey killed by bite, not talons); dark eyes and no bony brow ridge; long "
        "pointed wings; active flapping flight; a distinct moult sequence.",
        25, "Oligocene",
    ),
    "Psittacopasserae": (
        "Parrots + passerines: greatly enlarged forebrain, high cognition and "
        "(convergently, in true parrots and oscines) learned vocalisation controlled "
        "by dedicated forebrain song nuclei.",
        58, "Paleocene",
    ),
    "Passeriformes": (
        "Anisodactyl feet (three toes forward, one strong back toe) with an incumbent "
        "hallux and a tendon-locking perching mechanism; aegithognathous palate; a "
        "derived deep-plantar tendon arrangement; small body; altricial nestlings; "
        "distinctive coiled sperm.",
        47, "Eocene",
    ),
    "Psittaciformes": (
        "Strongly down-curved hooked bill with a mobile craniofacial hinge (prokinesis) "
        "and a broad fleshy cere; thick prehensile tongue; zygodactyl feet used like "
        "hands to manipulate food; large head and brain; powder down.",
        40, "Eocene",
    ),

    # ---- deep backbone: cellular life -> eukaryotes ----
    "Life": (
        "All cellular life descended from LUCA: a double-stranded DNA genome transcribed "
        "to RNA and translated by ribosomes; a nearly universal genetic code; ATP as "
        "energy currency; phospholipid-bilayer membranes.",
        3800, "Paleoarchean",
    ),
    "Bacteria": (
        "Prokaryotes with peptidoglycan (murein) cell walls and ester-linked fatty-acid "
        "membranes; bacterial-type RNA polymerase and 70S ribosomes; formyl-methionine "
        "translation start; usually one circular chromosome; no nucleus.",
        3500, "Paleoarchean",
    ),
    "Archaea": (
        "Prokaryotes with ether-linked, branched isoprenoid membrane lipids and cell "
        "walls lacking peptidoglycan; DNA replication, transcription and translation "
        "machinery resembling that of eukaryotes; histone-like proteins; many extremophiles.",
        3500, "Paleoarchean",
    ),
    "Eukaryota": (
        "Cells with a membrane-bound nucleus and endomembrane system; mitochondria from "
        "an alphaproteobacterial endosymbiont; an actin/tubulin cytoskeleton; linear "
        "chromosomes packaged on histones; 80S ribosomes; mitosis and meiotic sex.",
        1850, "Paleoproterozoic",
    ),
    "Discicristata": (
        "Eukaryotes whose mitochondria have distinctive discoid (plate-like) cristae; "
        "mostly free-living flagellates; unites Euglenozoa and Percolozoa.",
        1300, "Mesoproterozoic",
    ),
    "Euglenozoa": (
        "Flagellates with two flagella emerging from an apical pocket, a lattice-like "
        "paraxonemal rod alongside each axoneme, discoid cristae, and a proteinaceous "
        "pellicle of strips; includes euglenids and the kinetoplastids (trypanosomes).",
        900, "Neoproterozoic",
    ),
    "Percolozoa": (
        "'Shape-shifting' amoeboflagellates that switch between crawling amoeba and "
        "swimming flagellate forms; discoid mitochondrial cristae; eruptive lobose "
        "pseudopods; includes the brain-eating amoeba Naegleria.",
        600, "Neoproterozoic",
    ),
    "Orthokaryotes": (
        "Molecular clade joining the jakobids to all 'higher' eukaryotes (Neokaryotes); "
        "no unique morphological synapomorphy.",
        1750, "Paleoproterozoic",
    ),
    "Jakobea": (
        "Free-living bacterivorous biflagellates with a ventral feeding groove; retain "
        "the most gene-rich, bacteria-like mitochondrial genomes known in eukaryotes.",
        1400, "Mesoproterozoic",
    ),
    "Neokaryotes": (
        "Molecular clade uniting Bikonta/Diaphoretickes with Scotokaryotes; no "
        "morphological synapomorphy.",
        1700, "Paleoproterozoic",
    ),
    "Bikonta": (
        "Ancestrally biflagellate eukaryotes; encompasses most photosynthetic and "
        "free-living protist lineages; molecularly circumscribed, no morphological "
        "synapomorphy.",
        1650, "Mesoproterozoic",
    ),
    "Diaphoretickes": (
        "Huge molecular clade (Archaeplastida + SAR + Haptista + Cryptista and kin) "
        "containing most photosynthetic eukaryotes; no morphological synapomorphy.",
        1600, "Mesoproterozoic",
    ),
    "CAM": (
        "Molecular clade uniting Archaeplastida with Cryptista (and Microheliella); "
        "relevant to the spread of red-algal-derived plastids; no morphological "
        "synapomorphy.",
        1550, "Mesoproterozoic",
    ),
    "Pancryptista": (
        "Cryptomonads and their close relatives (kathablepharids, Palpitomonas); "
        "cryptomonads keep a nucleomorph (a relict red-algal nucleus) in the plastid, "
        "plus ejectisomes and a periplast of surface plates.",
        1100, "Mesoproterozoic",
    ),
    "Archaeplastida": (
        "Eukaryotes whose plastid came directly from primary endosymbiosis of a "
        "cyanobacterium (two envelope membranes, no periplastid compartment); red algae, "
        "green algae + land plants, and glaucophytes; starch/floridean-starch storage.",
        1550, "Mesoproterozoic",
    ),
    "Rhodaria": (
        "The red-algal lineage together with Picozoa and the predatory rhodelphids; "
        "ancestrally with phycobilisome light-harvesting antennae.",
        1300, "Mesoproterozoic",
    ),
    "Picozoa": (
        "Tiny (<3 um) marine heterotrophic flagellates whose cell is split by a groove "
        "into two compartments; feed on colloidal organic matter; have secondarily lost "
        "any plastid.",
        800, "Neoproterozoic",
    ),
    "Rhodophyta": (
        "Red algae: light-harvesting phycobiliproteins on phycobilisomes, floridean "
        "starch stored in the cytoplasm, unstacked thylakoids, pit connections between "
        "cells, and no flagella or centrioles at any life stage.",
        1150, "Mesoproterozoic",
    ),
    "Glaucophyta": (
        "Freshwater algae retaining the most cyanobacterium-like plastid (a 'muroplast' "
        "or cyanelle) with a vestigial peptidoglycan wall between its membranes and "
        "carboxysome-like inclusions; phycobilisomes.",
        1100, "Mesoproterozoic",
    ),
    "Viridiplantae": (
        "The green lineage (green algae + land plants): chlorophyll a and b, plastids "
        "with stacked thylakoids and no phycobilisomes, starch stored inside the plastid, "
        "and cellulose-rich cell walls.",
        1100, "Mesoproterozoic",
    ),
    "Chlorophyta": (
        "One of the two main green-algal clades, mostly marine; motile cells typically "
        "with two equal apical flagella on a cross-shaped (cruciate) root system; "
        "includes Chlamydomonas and sea lettuce (Ulva).",
        800, "Neoproterozoic",
    ),
    "Streptophyta": (
        "Charophyte green algae plus land plants; a broadened, asymmetrical flagellar "
        "root with a multilayered structure, and biochemical traits (class-I aldolase, "
        "Cu/Zn superoxide dismutase, glycolate oxidase) shared with land plants.",
        900, "Neoproterozoic",
    ),
    "Scotokaryotes": (
        "Molecular clade uniting Amorphea with Metamonada and CRuMs (broadly, the "
        "non-photosynthetic 'opisthokont side' of eukaryotes); no morphological "
        "synapomorphy.",
        1700, "Paleoproterozoic",
    ),
    "Metamonada": (
        "Anaerobic/microaerophilic flagellates that have lost classical mitochondria "
        "(reduced to hydrogenosomes or mitosomes); often many flagella and a stiff "
        "cytoskeletal axostyle; includes Giardia, Trichomonas and gut parabasalids.",
        1100, "Mesoproterozoic",
    ),
    "Podiata": (
        "Molecular clade (Amoebozoa + Obazoa + CRuMs) whose members ancestrally make "
        "pseudopodia ('feet') from a single anterior region; no strict morphological "
        "synapomorphy.",
        1650, "Mesoproterozoic",
    ),
    "CRuMs": (
        "Small clade named as an acronym for Collodictyonidae, Rigifilida and "
        "Mantamonas; ventrally-grooved or gliding flagellates with filose pseudopodia.",
        1200, "Mesoproterozoic",
    ),
    "Amorphea": (
        "Amoebozoa + Obazoa (amoebae, slime moulds, breviates, apusomonads, fungi and "
        "animals); cells ancestrally with a single posterior flagellum and/or amoeboid "
        "movement ('unikont' organisation); no strict morphological synapomorphy.",
        1500, "Mesoproterozoic",
    ),
    "Amoebozoa": (
        "Amoebae and slime moulds with blunt, tubular (lobose) pseudopodia and "
        "'fountain' cytoplasmic streaming; tubular mitochondrial cristae; at most a "
        "single posterior flagellum; includes Amoeba and Dictyostelium.",
        1300, "Mesoproterozoic",
    ),
    "Obazoa": (
        "Opisthokonta plus Breviatea and Apusomonadida; ancestrally biflagellate gliding "
        "cells; molecularly defined.",
        1300, "Mesoproterozoic",
    ),
    "Breviatea": (
        "Small anaerobic amoeboflagellates with two flagella and filose pseudopodia; "
        "mitochondrion-related organelles adapted to low oxygen.",
        900, "Neoproterozoic",
    ),
    "Apusomonadida": (
        "Gliding biflagellate bacterivores with a dorsal organic shell (theca) and a "
        "cytoplasmic sleeve wrapped around the base of the anterior flagellum.",
        900, "Neoproterozoic",
    ),
    "Opisthokonta": (
        "Cells that ancestrally swim with a single posterior flagellum and have "
        "flattened mitochondrial cristae; animals + fungi + their protist relatives; a "
        "fused multifunctional CAD gene is a molecular signature.",
        1100, "Mesoproterozoic",
    ),
    "Holomycota": (
        "Fungi together with nucleariid amoebae and the rozellids/Microsporidia; "
        "ancestrally filose amoebae with flattened cristae; the fungal chitin wall arises "
        "within this clade.",
        1050, "Mesoproterozoic",
    ),
    "Cristidiscoidea": (
        "Nucleariid filose amoebae plus Fonticula (a cellular slime mould); naked or "
        "scale-covered cells with fine radiating filopodia; sister to Fungi.",
        800, "Neoproterozoic",
    ),
    "Holozoa": (
        "Animals plus choanoflagellates, filastereans and ichthyosporeans; ancestrally "
        "a cell with a single flagellum encircled by a collar of microvilli, and a "
        "genetic tool-kit for cell adhesion and signalling later expanded in animals.",
        950, "Neoproterozoic",
    ),
    "Choanoflagellates": (
        "Solitary or colonial bacterivores, each cell driving water with one flagellum "
        "through a collar of actin-supported microvilli that strains out bacteria; the "
        "closest living relatives of animals.",
        800, "Neoproterozoic",
    ),

    # ---- basal animals ----
    "Metazoa": (
        "Multicellular heterotrophs that develop from an embryo; cells without walls, "
        "joined by cell junctions over a collagen basement membrane; shared adhesion and "
        "signalling proteins (cadherins, integrins); ancestrally with nerve and muscle "
        "cells.",
        650, "Neoproterozoic (Cryogenian)",
    ),
    "Porifera": (
        "Sessile filter-feeders with no true tissues, nerves or muscles; water is pumped "
        "by flagellated choanocyte chambers from surface pores to an osculum; a skeleton "
        "of mineral spicules and/or spongin; totipotent archaeocytes.",
        700, "Neoproterozoic (Cryogenian)",
    ),
    "Calcarea": (
        "Sponges whose spicules are calcium carbonate (calcite); the only sponges to "
        "show all three aquiferous grades (asconoid, syconoid, leuconoid); choanocytes "
        "with the nucleus at the flagellar base.",
        500, "Cambrian",
    ),
    "Hexactinellida": (
        "Deep-sea 'glass sponges' with a skeleton of six-rayed (triaxonic) silica "
        "spicules, often fused into a rigid lattice; body largely one giant multinucleate "
        "syncytium that conducts electrical impulses.",
        540, "Cambrian",
    ),
    "Demospongiae": (
        "The largest sponge class; skeleton of silica spicules that are never six-rayed "
        "and/or of spongin fibres; leuconoid canal system; includes bath sponges and "
        "rock-boring sponges.",
        650, "Neoproterozoic (Cryogenian)",
    ),
    "Eumetazoa": (
        "Animals with true epithelia sealed by belt junctions over a basement membrane, "
        "a gut, and ancestrally nerve and sensory cells arranged on a defined body "
        "symmetry.",
        600, "Neoproterozoic (Ediacaran)",
    ),
    "Ctenophora": (
        "Biradial gelatinous predators that swim using eight rows of fused giant cilia "
        "(comb rows) - the largest animals to move by cilia; sticky colloblast cells "
        "capture prey; an aboral statocyst; a muscular mesoglea.",
        620, "Neoproterozoic (Ediacaran)",
    ),
    "ParaHoxozoa": (
        "Placozoans, cnidarians and bilaterians; possess ParaHox genes and an expanded "
        "Hox / NK homeobox tool-kit used to pattern the body axis.",
        610, "Neoproterozoic (Ediacaran)",
    ),
    "Cnidaria": (
        "Radial animals with one gut opening, two body layers, and stinging cnidocytes "
        "that fire a coiled nematocyst thread; a nerve net; a life cycle alternating "
        "polyp and medusa.",
        595, "Neoproterozoic (Ediacaran)",
    ),
    "Anthozoa": (
        "Cnidarians with only the polyp stage (no medusa); the gut is partitioned by "
        "mesenteries and opens through a folded pharynx (actinopharynx); linear "
        "mitochondrial DNA; sea anemones and corals.",
        560, "Neoproterozoic (Ediacaran)",
    ),
    "Hexacorallia": (
        "Anthozoans whose tentacles and mesenteries come in multiples of six; simple "
        "unarmoured nematocysts; includes reef-building stony corals (aragonite "
        "skeleton), sea anemones and zoanthids.",
        500, "Cambrian",
    ),
    "Actinaria": (
        "Skeleton-less solitary hexacorals (sea anemones) that attach and burrow with a "
        "muscular pedal disc; a crown of tentacles; many have defensive acontia or "
        "elongated catch-tentacles.",
        400, "Devonian",
    ),
    "Octocorallia": (
        "Colonial anthozoans whose polyps always have exactly eight pinnate (feathered) "
        "tentacles and eight mesenteries; an internal skeleton of separate calcite "
        "sclerites; soft corals, sea fans and sea pens.",
        400, "Devonian",
    ),
    "Endocnidozoa": (
        "Obligately parasitic cnidarians (Myxozoa + Polypodium) reduced to a few cells, "
        "yet retaining polar capsules homologous to nematocysts.",
        510, "Cambrian",
    ),
    "Myxozoa": (
        "Microscopic endoparasites of fish and annelids; the animal is reduced to spores "
        "of a few cells bearing coiled polar filaments; among the smallest animal "
        "genomes; no gut, nerves or body axis.",
        400, "Devonian",
    ),
    "Polypodiozoa": (
        "A single species that parasitises the eggs of sturgeon and paddlefish; its "
        "free-living stage is an inside-out, tentacled 'stolon' that walks on its "
        "tentacles; retains true nematocysts.",
        400, "Devonian",
    ),
    "Medusozoa": (
        "Cnidarians whose life cycle includes a free medusa budded from the polyp; a "
        "velum or velarium aids jet propulsion; linear mitochondrial chromosomes.",
        580, "Neoproterozoic (Ediacaran)",
    ),
    "Scyphozoa": (
        "'True jellyfish': a large dominant medusa and a reduced polyp (scyphistoma) "
        "that releases young medusae by transverse strobilation; gastric filaments; "
        "four-part symmetry; rhopalia as sense organs.",
        500, "Cambrian",
    ),
    "Cubozoa": (
        "'Box jellies': a cuboidal medusa with camera-type lensed eyes on four rhopalia, "
        "muscular pedalia carrying the tentacles, a true velarium, and potent venom; the "
        "polyp metamorphoses entirely into a single medusa.",
        300, "Carboniferous",
    ),
    "Hydrozoa": (
        "Medusozoans usually with a colonial polyp stage and small medusae budded from "
        "the body wall (not by strobilation); the medusa has a true velum; gonads are "
        "epidermal; includes Hydra, siphonophores and fire corals.",
        540, "Cambrian",
    ),
    "Staurozoa": (
        "'Stalked jellyfish' with no free-swimming medusa: a funnel-shaped body attached "
        "by an adhesive basal disc, combining polyp and medusa features, with eight "
        "clusters of knobbed tentacles.",
        400, "Devonian",
    ),

    # ---- Bilateria and protostomes ----
    "Bilateria": (
        "Animals with bilateral symmetry (at least in the larva), three germ layers "
        "including a true mesoderm, anterior concentration of nerves and sense organs "
        "(cephalisation), and a through-gut in most; Hox genes in a colinear cluster.",
        575, "Neoproterozoic (Ediacaran)",
    ),
    "Xenacoelomorpha": (
        "Small simple worms with no through-gut (a blind sac or none), no discrete "
        "excretory organs, a basiepidermal nerve net or paired cords, and a distinctive "
        "ciliary rootlet; includes acoels and Xenoturbella.",
        555, "Cambrian",
    ),
    "Nephrozoa": (
        "Bilaterians with dedicated excretory organs (protonephridia or metanephridia) "
        "and, ancestrally, a through-gut with mouth and anus and a coelom; splits into "
        "protostomes and deuterostomes.",
        565, "Neoproterozoic (Ediacaran)",
    ),
    "Protostomia": (
        "Bilaterians in which (ancestrally) the blastopore becomes the mouth, cleavage "
        "is spiral, the mesoderm forms by schizocoely, and the main nerve cords run "
        "ventrally with a circumoesophageal ring.",
        555, "Cambrian",
    ),
    "Ecdysozoa": (
        "Protostomes with a cuticle (often chitinous) shed by moulting under hormonal "
        "control; no locomotory cilia on the body surface; growth in steps between "
        "moults; includes arthropods, nematodes, tardigrades.",
        545, "Cambrian",
    ),
    "Spiralia": (
        "Protostomes ancestrally with spiral cleavage and, in many, a trochophore "
        "larva; body surface ciliated; includes molluscs, annelids, flatworms, "
        "brachiopods and rotifers.",
        550, "Cambrian",
    ),
    "Arthropoda": (
        "Ecdysozoans with a segmented body and jointed limbs, a hardened chitinous "
        "exoskeleton, an open haemocoel with a dorsal heart, a ventral nerve cord with "
        "segmental ganglia, and compound eyes.",
        535, "Cambrian",
    ),
    "Chelicerata": (
        "Arthropods whose body is a prosoma (bearing chelicerae, pedipalps and four "
        "leg pairs) plus an opisthosoma; no antennae; no mandibles; often book lungs or "
        "book gills; extra-oral digestion.",
        515, "Cambrian",
    ),
    "Arachnida": (
        "Mostly terrestrial chelicerates with four pairs of walking legs, book lungs "
        "and/or tracheae, malpighian tubules, and often silk or venom glands; pedipalps "
        "modified for sensing or prey capture.",
        480, "Ordovician",
    ),
    "Scorpiones": (
        "Arachnids with large grasping pedipalp pincers, a segmented tail (metasoma) "
        "ending in a venomous sting, comb-like pectines under the body, and fluorescence "
        "under UV light; ancient, little changed since the Silurian.",
        430, "Silurian",
    ),
    "Xiphosura": (
        "Marine chelicerates with a large horseshoe-shaped carapace, a hinged "
        "opisthosoma, book gills, a long spike-like telson, and blue copper-based "
        "haemolymph; 'living fossils'.",
        300, "Carboniferous",
    ),
    "Mandibulata": (
        "Arthropods bearing a pair of mandibles for biting/chewing, one or two pairs of "
        "maxillae, antennae on the first head segment, and (ancestrally) compound eyes "
        "with a crystalline cone.",
        535, "Cambrian",
    ),
    "Myriapoda": (
        "Terrestrial mandibulates with a head plus a long homonomous trunk of many "
        "leg-bearing segments, one pair of antennae, tracheae, malpighian tubules, and "
        "Toemoesvary organs for sensing humidity.",
        430, "Silurian",
    ),
    "Chilopoda": (
        "Fast predatory myriapods, dorsoventrally flattened, with one leg pair per "
        "trunk segment and a pair of venomous fang-like forcipules (modified first "
        "legs); long antennae.",
        340, "Carboniferous",
    ),
    "Diplopoda": (
        "Slow detritivorous myriapods, cylindrical, with two leg pairs per apparent "
        "segment (diplosegments), short antennae, and defensive glands (some producing "
        "cyanide); among the first animals on land.",
        420, "Silurian",
    ),
    "Pancrustacea": (
        "The clade of crustaceans plus hexapods (insects); shared neural and eye "
        "developmental characters and a nauplius-type larva ancestrally.",
        520, "Cambrian",
    ),
    "Crustacea": (
        "Mostly aquatic mandibulates with two pairs of antennae, biramous (two-branched) "
        "limbs, gills, a nauplius larva, and calcified cuticle in many; crabs, shrimp, "
        "copepods, barnacles, woodlice.",
        510, "Cambrian",
    ),
    "Hexapoda": (
        "Six-legged pancrustaceans with the body in head, thorax (three leg-bearing "
        "segments) and abdomen; one pair of antennae; tracheal breathing; malpighian "
        "tubules; wings in most insects.",
        480, "Ordovician",
    ),
    "Nematoda": (
        "Unsegmented round worms with a tough collagen cuticle moulted four times, only "
        "longitudinal body-wall muscle (so they thrash sinusoidally), a fluid-filled "
        "pseudocoel at high pressure, and eutely (fixed cell number).",
        530, "Cambrian",
    ),
    "Lophotrochozoa": (
        "Spiralians characterised by a ciliated tentacular feeding crown (lophophore) "
        "in some groups and/or a trochophore larva; molluscs, annelids, brachiopods, "
        "bryozoans, nemerteans.",
        550, "Cambrian",
    ),
    "Mollusca": (
        "Unsegmented coelomates with a muscular foot, a dorsal visceral mass covered by "
        "a mantle that secretes a calcareous shell, a mantle cavity with gills "
        "(ctenidia), and usually a rasping radula.",
        540, "Cambrian",
    ),
    "Gastropods": (
        "Molluscs that undergo torsion as larvae, twisting the visceral mass 180 deg so "
        "the mantle cavity faces forward; a single (often coiled) shell; a well-developed "
        "head with tentacles and a radula; snails, slugs, limpets.",
        500, "Cambrian",
    ),
    "Bivalves": (
        "Molluscs with a two-part hinged shell closed by adductor muscles, no head or "
        "radula, large sheet-like gills used for filter feeding, and a hatchet-shaped "
        "burrowing foot; clams, mussels, oysters, scallops.",
        490, "Cambrian",
    ),
    "Cephalopoda": (
        "Active marine molluscs with the foot modified into arms/tentacles around the "
        "mouth, a chambered buoyancy shell (external, internal or lost), jet propulsion "
        "from the funnel, a beak, closed circulation, and large image-forming eyes.",
        485, "Cambrian",
    ),
    "Coleoidea": (
        "Cephalopods with the shell reduced, internalised (gladius, cuttlebone, "
        "phragmocone) or lost; eight or ten sucker-bearing arms; chromatophore skin "
        "for instant colour and pattern change; large complex brains and camera eyes; "
        "an ink sac; short lives ending in a single reproductive event.",
        240, "Triassic",
    ),
    "Nautiloidea": (
        "The only living cephalopods that keep a large external coiled shell divided "
        "into gas-filled buoyancy chambers linked by a siphuncle; up to ~90 small "
        "suckerless tentacles; pinhole eyes with no lens; a leathery hood; slow-growing "
        "and long-lived - 'living fossils'.",
        35, "Eocene",
    ),
    "Octopodiformes": (
        "Eight-armed coleoids - octopuses and the vampire squid - with the shell lost "
        "or vestigial, suckers usually without stalks, the most elaborate brains and "
        "camera eyes of any invertebrate, skin chromatophores for instant camouflage, "
        "and (in octopuses) a benthic, den-dwelling life.",
        160, "Jurassic",
    ),
    "Decapodiformes": (
        "Ten-appendage coleoids - squids and cuttlefishes - with eight arms plus two "
        "longer retractile prey-catching tentacles, an internal chitinous pen or a "
        "chambered cuttlebone, lateral fins for steady swimming, fast jet escape, and a "
        "streamlined pelagic body.",
        160, "Jurassic",
    ),
    "Annelida": (
        "Segmented worms with a body of repeated ring-like segments separated by septa, "
        "a spacious coelom acting as a hydrostatic skeleton, chitinous bristles "
        "(chaetae), and a closed circulatory system.",
        540, "Cambrian",
    ),
    "Crassiclitellata": (
        "Terrestrial burrowing annelids (oligochaetes) with few chaetae, no parapodia "
        "or head appendages, a glandular clitellum that secretes an egg cocoon, "
        "hermaphroditism, and a gut adapted to processing soil.",
        180, "Jurassic",
    ),
    "Hirudinea": (
        "Predatory or blood-feeding annelids with a fixed 34-segment body, an anterior "
        "and a large posterior sucker, no chaetae, a reduced coelom filled with tissue, "
        "a clitellum, and (in many) anticoagulant saliva.",
        200, "Jurassic",
    ),
    "Platyhelminthes": (
        "Flatworms: dorsoventrally flattened, unsegmented, with no coelom, no anus (a "
        "branched blind gut or none), gas exchange across the skin, protonephridia with "
        "flame cells, and strong powers of regeneration.",
        500, "Cambrian",
    ),

    # ---- deuterostomes: echinoderms, hemichordates, early chordates ----
    "Deuterostomia": (
        "Bilaterians in which (ancestrally) the blastopore becomes the anus and the "
        "mouth forms secondarily, cleavage is radial, the mesoderm and coelom form by "
        "enterocoely, and pharyngeal gill slits are present.",
        560, "Neoproterozoic (Ediacaran)",
    ),
    "Ambulacraria": (
        "Echinoderms plus hemichordates; a three-part coelom (proto-, meso-, "
        "metacoel), a dipleurula-type ciliated larva, and (ancestrally) a water "
        "vascular system derived from the mesocoel.",
        550, "Cambrian",
    ),
    "Echinodermata": (
        "Marine deuterostomes with fivefold (pentaradial) adult symmetry from a "
        "bilateral larva, a calcite endoskeleton of porous ossicles (stereom), a water "
        "vascular system operating tube feet, and mutable collagenous tissue.",
        520, "Cambrian",
    ),
    "Crinoidea": (
        "Stalked or free 'sea lilies' and feather stars: mouth and anus both face "
        "upward on a cup (calyx) with feeding arms bearing a ciliated food groove; the "
        "only living echinoderms with the mouth on the upper surface.",
        240, "Triassic",
    ),
    "Eleutherozoa": (
        "Free-living echinoderms (all living classes except crinoids); mouth directed "
        "downward or to one side; tube feet used for locomotion; a madreporite opening "
        "the water vascular system to the exterior.",
        490, "Cambrian",
    ),
    "Asterozoa": (
        "Star-shaped echinoderms with arms radiating from a central disc: sea stars and "
        "brittle stars; ambulacral grooves running out along the underside of each arm.",
        480, "Ordovician",
    ),
    "Asteroidea": (
        "Sea stars: broad arms merging into the disc, open ambulacral grooves with "
        "suckered tube feet, the ability to evert the stomach to feed externally, and "
        "strong arm regeneration.",
        240, "Triassic",
    ),
    "Ophiuroidea": (
        "Brittle stars: a sharply set-off central disc and long, snake-like jointed "
        "arms moved by 'vertebral' ossicles; tube feet without suckers, used for feeding "
        "not walking; the arms writhe for locomotion.",
        200, "Jurassic",
    ),
    "Echinozoa": (
        "Globular or cylindrical echinoderms with no arms: sea urchins and sea "
        "cucumbers; body built on five ambulacra running from mouth to the opposite pole.",
        490, "Cambrian",
    ),
    "Echinoidea": (
        "Sea urchins and sand dollars: ossicles fused into a rigid test bearing movable "
        "spines on ball-and-socket joints, a five-toothed jaw apparatus (Aristotle's "
        "lantern), and pedicellariae.",
        250, "Triassic",
    ),
    "Holothuroidea": (
        "Sea cucumbers: elongated along the oral-aboral axis, lying on one side; the "
        "skeleton reduced to microscopic ossicles in a leathery body wall; a ring of "
        "feeding tentacles (modified tube feet); respiratory trees; defensive evisceration.",
        350, "Carboniferous",
    ),
    "Hemichordata": (
        "Marine worms (acorn worms) and colonial pterobranchs with a body of proboscis, "
        "collar and trunk, pharyngeal gill slits, a stomochord (a buccal diverticulum "
        "once thought a notochord), and a dorsal collar nerve cord.",
        500, "Cambrian",
    ),
    "Chordata": (
        "Animals with, at some life stage, a dorsal notochord, a hollow dorsal nerve "
        "cord, pharyngeal slits, an endostyle/thyroid, and a post-anal tail with "
        "segmented (myomeric) muscle blocks.",
        545, "Cambrian",
    ),
    "Cephalochordata": (
        "Small fish-like filter-feeders (amphioxus) that keep all chordate features as "
        "adults: a notochord running the whole body length (into the head), no true "
        "head, brain or paired eyes, and a large pharyngeal basket in an atrium.",
        180, "Jurassic",
    ),
    "Olfactores": (
        "Tunicates plus vertebrates; an expanded forebrain region with paired sensory "
        "placodes (olfactory and otic), migratory neural-crest-like cells, and a "
        "muscular pumping heart.",
        545, "Cambrian",
    ),
    "Tunicata": (
        "Marine filter-feeders (sea squirts, salps) enclosed in a cellulose 'tunic'; a "
        "tadpole larva with notochord and nerve cord that is usually resorbed at "
        "metamorphosis into a sessile adult with a huge pharyngeal basket.",
        400, "Devonian",
    ),
    "Vertebrata": (
        "Chordates with a bony or cartilaginous vertebral column around the nerve cord, "
        "a cranium enclosing a tripartite brain, paired special sense organs, neural "
        "crest, ectodermal placodes, and a chambered heart.",
        515, "Cambrian",
    ),
    "Cyclostomata": (
        "Living jawless vertebrates (lampreys + hagfishes): no jaws, no paired fins, a "
        "single median nostril, a cartilaginous skeleton with no bone, a notochord "
        "retained through life, and a rasping keratinous tongue apparatus.",
        480, "Ordovician",
    ),
    "Petromyzontiformes": (
        "Jawless cyclostomes with a toothed sucker-disc mouth and piston-like tongue "
        "used to rasp flesh or attach; seven pairs of gill pouches; a well-developed eye "
        "and pineal eye; a larval (ammocoete) filter-feeding stage.",
        180, "Jurassic",
    ),
    "Myxiniformes": (
        "Jawless cyclostomes that secrete enormous amounts of defensive slime; a "
        "partial cranium but no vertebrae or eyes lens; a single nasohypophyseal duct "
        "opening to the pharynx; knotting behaviour; burrowing scavengers.",
        150, "Cretaceous (Early)",
    ),
    "Gnathostomata": (
        "Jawed vertebrates: jaws from the first pharyngeal arch, teeth with dentine and "
        "enamel, paired pectoral and pelvic fins/limbs, three semicircular canals, a "
        "myelin sheath on nerves, and an adaptive immune system.",
        460, "Ordovician",
    ),
    "Chondrichthyes": (
        "Cartilaginous fishes with a prismatic calcified cartilage skeleton, no true "
        "bone, tooth-like placoid scales (dermal denticles), teeth in replacement rows, "
        "claspers for internal fertilisation, and no swim bladder.",
        415, "Silurian",
    ),
    "Elasmobranchii": (
        "Sharks, skates and rays: five to seven separate gill slits, a spiracle, a "
        "rigid upper jaw only loosely attached to the braincase (hyostyly), and "
        "ampullae of Lorenzini for electroreception.",
        285, "Permian",
    ),
    "Selachii": (
        "Modern sharks: a fusiform body, pectoral fins not fused to the head, gill slits "
        "on the sides, a heterocercal tail, and highly protrusible jaws in most.",
        250, "Triassic",
    ),
    "Batomorphii": (
        "Skates and rays: dorsoventrally flattened, pectoral fins hugely enlarged and "
        "fused to the head as a disc, gill slits on the underside, eyes and spiracles on "
        "top, and (in many) a whip-like tail with a venomous barb.",
        200, "Jurassic",
    ),
    "Holocephali": (
        "Chimaeras ('ratfish'): the upper jaw fused to the braincase (holostyly), "
        "tooth plates instead of teeth, a single gill opening under a fleshy operculum, "
        "naked skin, a venomous dorsal spine, and a frontal clasper in males.",
        170, "Jurassic",
    ),
    "Osteichthyes": (
        "Bony fishes (and their tetrapod descendants): an ossified endoskeleton, dermal "
        "bones roofing the skull and forming jaw margins, lungs or a swim bladder from "
        "the gut, and (ancestrally) enamel-covered ganoid scales.",
        430, "Silurian",
    ),
    "Actinopterygii": (
        "Ray-finned fishes: fins webbed between bony rays (lepidotrichia) with little "
        "muscle extending into them, a single dorsal fin ancestrally, and a swim bladder "
        "for buoyancy; by far the most species-rich vertebrate group.",
        385, "Devonian",
    ),
    "Sarcopterygii": (
        "Lobe-finned fishes and tetrapods: paired fins/limbs with a single proximal "
        "bone articulating with the girdle and muscular, bony fin lobes; cosmoid scales "
        "ancestrally; enamel on the teeth.",
        420, "Silurian",
    ),
    "Actinistia": (
        "Coelacanths: a three-lobed (trilobed) tail with a small central lobe, a "
        "hinged intracranial joint letting the front of the skull swing up, an "
        "oil-filled notochord in place of vertebral centra, and paired lobed fins; "
        "'living fossils'.",
        400, "Devonian",
    ),
    "Rhipidistia": (
        "Lungfishes plus tetrapods; functional lungs used for air-breathing, internal "
        "nostrils (choanae) in the tetrapod line, and a two-part fin/limb skeleton "
        "beyond the first bone.",
        415, "Silurian",
    ),
    "Dipnoi": (
        "Lungfishes: obligate or facultative air-breathers with paired or single lungs, "
        "crushing tooth plates fused to the palate, an autostylic jaw (no separate upper "
        "jaw bone), a largely cartilaginous braincase, and aestivation in mud.",
        280, "Permian",
    ),
    "Tetrapoda": (
        "Four-limbed vertebrates with digits, a neck separating head from pectoral "
        "girdle (shoulder freed from the skull), a sacrum anchoring the pelvis to the "
        "spine, distinct wrist/ankle joints, and lungs as the primary adult respiration.",
        345, "Carboniferous",
    ),
    "Lissamphibia": (
        "Living amphibians (Lissamphibia): a moist, permeable, glandular skin used in "
        "gas exchange, pedicellate bicuspid teeth, a papilla amphibiorum in the ear, "
        "green rods in the retina, and (usually) an aquatic larva that metamorphoses.",
        290, "Permian",
    ),
    "Anura": (
        "Frogs and toads: no tail as adults, a short spine with a long rod-like "
        "urostyle, hugely elongated hindlimbs and fused ankle bones for jumping, a fused "
        "radioulna and tibiofibula, and a large eardrum; vocal males.",
        200, "Jurassic",
    ),
    "Caudata": (
        "Salamanders and newts: a lizard-like body with a long tail kept as adults, "
        "four limbs of roughly equal size held out to the sides, the ability to "
        "regenerate limbs and tail, and internal fertilisation via a spermatophore in "
        "most.",
        170, "Jurassic",
    ),
    "Gymnophiona": (
        "Caecilians: limbless, near-blind burrowing (or aquatic) amphibians with a "
        "ringed (annulated) body, a solid braincase, a pair of chemosensory tentacles "
        "between eye and nostril, and dermal scales in the skin folds of many.",
        170, "Jurassic",
    ),

    # ---- Amniota: reptiles ----
    "Amniota": (
        "Tetrapods that reproduce on land via an amniotic egg (amnion, chorion, "
        "allantois) or its live-bearing derivative; a waterproof keratinised "
        "(cornified) skin; costal (rib) breathing; no aquatic larval stage.",
        320, "Carboniferous",
    ),
    "Reptilia": (
        "Sauropsid amniotes with scaly skin of beta-keratin, uricotelic excretion, a "
        "largely three-chambered heart (four-chambered in archosaurs), and eggs with "
        "little yolk-free albumen; ancestrally ectothermic.",
        280, "Permian",
    ),
    "Lepidosauria": (
        "Reptiles with overlapping horny scales shed in patches or whole, a "
        "transverse cloacal slit, paired hemipenes in males (or none), and (in "
        "squamates) determinate skull kinesis; tuatara plus lizards and snakes.",
        250, "Triassic",
    ),
    "Rhynchocephalia": (
        "Represented today only by the tuatara (Sphenodon) of New Zealand: a "
        "lizard-like reptile keeping a complete lower temporal bar, a beak-like "
        "premaxilla, teeth fused to the jaw edge in a single wedge row (acrodont), a "
        "well-developed parietal 'third eye', very slow growth, and no copulatory organ.",
        240, "Triassic",
    ),
    "Squamata": (
        "Lizards, snakes and amphisbaenians: a highly kinetic skull that has lost the "
        "lower temporal bar, paired eversible hemipenes, a forked or notched tongue "
        "serving a Jacobson's (vomeronasal) organ, skin shed periodically, and "
        "(ancestrally) the ability to shed the tail to escape.",
        190, "Jurassic",
    ),
    "Archelosauria": (
        "Turtles plus archosaurs (crocodiles and birds); shared microRNA and "
        "chromosomal characters; ancestrally with a diapsid skull (secondarily closed "
        "in turtles).",
        255, "Permian",
    ),
    "Archosauria": (
        "'Ruling reptiles': an antorbital fenestra in the skull, teeth set in sockets "
        "(thecodont), a four-chambered heart, and often an upright limb posture; "
        "crocodile-line and bird-line reptiles.",
        250, "Triassic",
    ),
    "Crocodylia": (
        "Semi-aquatic archosaurs with heavy bony-plated (osteoderm) armour, a secondary "
        "bony palate, a sprawling-to-'high walk' gait, a muscular valved four-chambered "
        "heart, parental care, and a slap-shut death roll.",
        95, "Cretaceous (Late)",
    ),
    "Testudines": (
        "Turtles: a shell of fused ribs and vertebrae (carapace) plus a plastron, with "
        "the limb girdles uniquely inside the ribcage; no teeth (a horny beak); the "
        "neck retracted sideways (pleurodires) or vertically (cryptodires).",
        200, "Triassic",
    ),
    "Pleurodira": (
        "Side-necked turtles: the neck folds horizontally to tuck the head sideways "
        "under the shell rim; the pelvis is fused to both carapace and plastron; "
        "freshwater, Southern Hemisphere (South America, Africa, Australia).",
        150, "Jurassic",
    ),
    "Cryptodira": (
        "Hidden-necked turtles: the neck retracts in a vertical S-bend to pull the head "
        "straight back into the shell; the pelvis is not fused to the shell; sea "
        "turtles, tortoises, snapping turtles, softshells - most living turtle diversity.",
        165, "Jurassic",
    ),

    # ---- Mammalia ----
    "Mammalia": (
        "Amniotes with hair, mammary glands nursing the young with milk, three middle "
        "ear ossicles (malleus, incus, stapes) and a single lower-jaw bone (dentary), "
        "heterodont teeth replaced once, a muscular diaphragm, and endothermy.",
        180, "Jurassic",
    ),
    "Monotremata": (
        "Egg-laying mammals: a single cloacal opening, a leathery-shelled egg, milk "
        "oozing from mammary patches (no nipples), a reptile-like shoulder girdle, "
        "electroreceptive bills/snouts, and venom spurs in males (functional in the "
        "platypus).",
        60, "Paleocene",
    ),
    "Ornithorhynchidae": (
        "A semi-aquatic monotreme with a soft electroreceptive duck-like bill, dense "
        "waterproof fur, webbed forefeet, a beaver-like tail, no teeth as an adult "
        "(horny pads), and a venomous ankle spur in males.",
        20, "Miocene",
    ),
    "Tachyglossidae": (
        "Terrestrial monotremes ('spiny anteaters') covered in protective spines, with "
        "a tubular toothless snout, a long sticky tongue for ants and termites, powerful "
        "digging claws, and a temporary pouch that holds the egg.",
        15, "Miocene",
    ),
    "Theria": (
        "Live-bearing mammals (marsupials + placentals): no shelled egg, nipples for "
        "suckling, a mobile scapula with the coracoid reduced to a process, teeth "
        "replaced in only one set of positions, and (ancestrally) three-cusped molars "
        "of tribosphenic form.",
        160, "Jurassic",
    ),
    "Marsupialia": (
        "Therians that give birth to tiny embryonic young which finish development "
        "attached to a teat, usually in a pouch (marsupium); epipubic bones; a "
        "choriovitelline (yolk-sac) placenta; a distinctive tooth count and inflected "
        "jaw angle.",
        80, "Cretaceous (Late)",
    ),
    "Eutheria": (
        "Placental mammals: a long pregnancy nourished by a chorioallantoic placenta, "
        "no epipubic bones (allowing a distensible abdomen), a corpus callosum linking "
        "the brain hemispheres, and relatively well-developed newborns.",
        75, "Cretaceous (Late)",
    ),
    "Atlantogenata": (
        "Placentals of Gondwanan (South American + African) origin: the xenarthrans "
        "plus Afrotheria; the grouping is mainly molecular and biogeographic.",
        70, "Paleocene",
    ),
    "Xenarthra": (
        "South American placentals with extra ('xenarthrous') articulations between the "
        "lumbar vertebrae, a low metabolic rate and low body temperature, simplified "
        "peg-like teeth without enamel (or none), and often bony dermal armour.",
        65, "Paleocene",
    ),
    "Cingulata": (
        "Armoured xenarthrans (armadillos, extinct glyptodonts) with a shell of bony "
        "dermal plates (osteoderms) covered in horn, often with movable bands; strong "
        "digging forelimbs and simple peg teeth.",
        45, "Eocene",
    ),
    "Pilosa": (
        "The 'hairy' xenarthrans: anteaters and sloths; no armour, reduced or absent "
        "dentition, powerful curved claws requiring a knuckle- or edge-walking gait, "
        "and a very low metabolic rate.",
        55, "Paleocene",
    ),
    "Vermilingua": (
        "Anteaters: a toothless tubular skull, a long protrusible worm-like tongue "
        "flicked rapidly and coated in sticky saliva, huge digging foreclaws (walking "
        "on the knuckles), a low body temperature, and a keen sense of smell.",
        40, "Eocene",
    ),
    "Folivora": (
        "Sloths: slow arboreal (or, when extinct, giant ground) xenarthrans with long "
        "hooked claws for hanging upside down, extra neck vertebrae in some, a "
        "multi-chambered stomach for leaves, very low metabolism, and grooved hair that "
        "hosts algae.",
        30, "Oligocene",
    ),
    "Afrotheria": (
        "A placental clade of African origin - elephants, hyraxes, sea cows, "
        "aardvark, tenrecs, elephant shrews, golden moles; unusually many "
        "thoracolumbar vertebrae, late-erupting permanent teeth, and testes that stay "
        "in the abdomen (testicondy).",
        75, "Cretaceous (Late)",
    ),
    "Boreoeutheria": (
        "The 'northern' placentals: Laurasiatheria (carnivores, ungulates, bats, "
        "etc.) plus Euarchontoglires (primates, rodents, rabbits); mainly a molecular "
        "clade, of Laurasian origin.",
        72, "Cretaceous (Late)",
    ),

    # ---- Laurasiatheria ----
    "Laurasiatheria": (
        "A large placental clade of Laurasian origin - insectivores (shrews, moles), "
        "bats, carnivores, pangolins and hoofed mammals (including whales); united "
        "chiefly by molecular data.",
        72, "Cretaceous (Late)",
    ),
    "Eulipotyphla": (
        "Small, mostly insectivorous laurasiatheres - shrews, moles, hedgehogs, "
        "solenodons; a long pointed mobile snout, small eyes, primitive sharp-cusped "
        "(zalambdodont/dilambdodont) molars, and a reduced or absent caecum; venomous "
        "saliva in several.",
        70, "Paleocene",
    ),
    "Scrotifera": (
        "The laurasiatheres outside Eulipotyphla (bats, carnivores, pangolins, "
        "ungulates); named for the ancestral presence of a post-penile scrotum; a "
        "molecular clade.",
        70, "Paleocene",
    ),
    "Chiroptera": (
        "The only truly flying mammals: forelimbs modified into wings with a skin "
        "membrane (patagium) stretched between very long finger bones, a keeled sternum, "
        "hind feet turned to hang upside down, and laryngeal echolocation in most.",
        62, "Paleocene",
    ),
    "Yinpterochiroptera": (
        "One of the two main bat clades: the large non-echolocating Old World fruit bats "
        "plus several echolocating families (horseshoe bats, false vampires); some fruit "
        "bats use tongue-click echolocation.",
        58, "Paleocene",
    ),
    "Yangochiroptera": (
        "The other main bat clade: all laryngeally echolocating, mostly insectivorous "
        "families (vesper bats, free-tailed bats, leaf-nosed bats of the New World, "
        "true vampire bats).",
        55, "Paleocene",
    ),
    "Ferungulata": (
        "Carnivorans and pangolins together with the hoofed mammals (odd- and "
        "even-toed ungulates, including cetaceans); a molecular grouping within "
        "Scrotifera.",
        76, "Cretaceous (Late)",
    ),
    "Ferae": (
        "Carnivora plus Pholidota (pangolins); ancestrally predatory or "
        "insectivorous mammals; share features of the ankle and skull base.",
        73, "Cretaceous (Late)",
    ),
    "Carnivora": (
        "Placental predators (and their omnivore/herbivore descendants) with a pair of "
        "shearing carnassial teeth (last upper premolar against first lower molar), "
        "usually large canines, a reduced or fused clavicle, and a well-developed "
        "sense of smell.",
        55, "Paleocene",
    ),
    "Caniformia": (
        "Dog-line carnivorans: a longer snout, more numerous and less specialised "
        "teeth, usually non-retractile claws, a single-chambered auditory bulla, and a "
        "baculum; dogs, bears, weasels, raccoons, red panda, and the seals.",
        48, "Eocene",
    ),
    "Canidae": (
        "Dogs, wolves and foxes: long-legged, digitigrade endurance hunters with blunt "
        "non-retractile claws and a long muzzle carrying many teeth (shearing "
        "carnassials but also crushing molars for omnivory); cooperative pack living "
        "and pair bonding in many.",
        12, "Miocene",
    ),
    "Arctoidea": (
        "The 'bear-like' caniforms - bears, pinnipeds, and the weasel/raccoon/skunk/"
        "red-panda group; united by features of the ossified auditory bulla and skull "
        "base, and an ancestrally plantigrade foot.",
        43, "Eocene",
    ),
    "Ursidae": (
        "Bears: the largest land carnivorans, plantigrade with five non-retractile "
        "claws, a short tail and long snout; flat crushing molars and reduced "
        "carnassials for a mostly omnivorous or herbivorous diet (the polar bear "
        "reverted to meat); delayed implantation and winter denning.",
        20, "Miocene",
    ),
    "Musteloidea": (
        "Weasels, otters, badgers, raccoons, skunks and the red panda: mostly small, "
        "short-legged, elongated caniforms with well-developed anal scent glands "
        "(extreme in skunks), often high metabolic rates and delayed implantation, "
        "ranging from hypercarnivores to omnivores and the bamboo-eating red panda.",
        33, "Oligocene",
    ),
    "Feliformia": (
        "Cat-like carnivorans (Feliformia): a shorter face, fewer teeth with more "
        "specialised carnassials, often retractile claws, a double-chambered bony "
        "auditory bulla, and grooming with the forepaw; cats, hyenas, mongooses, civets.",
        45, "Eocene",
    ),
    "Pinnipedia": (
        "Marine caniform carnivorans - seals, sea lions, walrus - with all four limbs "
        "modified into flippers, a streamlined blubber-insulated body, reduced external "
        "ears or none, and the ability to nurse and haul out on land or ice.",
        25, "Oligocene",
    ),
    "Pholidota": (
        "Pangolins: toothless insectivores covered in large overlapping scales of "
        "agglutinated hair, a long sticky tongue rooted near the pelvis, powerful "
        "digging foreclaws, no teeth (food ground in a keratinous 'gizzard' stomach), "
        "and the ability to roll into a ball.",
        35, "Eocene",
    ),
    "Euungulata": (
        "Hoofed placental mammals - odd-toed (horses, tapirs, rhinos) and even-toed "
        "(pigs, ruminants, hippos, whales); the digit tips bear hooves, limbs are built "
        "for running with reduced side toes, and most are herbivores with complex "
        "stomachs or an enlarged caecum.",
        73, "Cretaceous (Late)",
    ),
    "Perissodactyla": (
        "Odd-toed ungulates: body weight borne on the central (third) toe, a "
        "hindgut fermentation system in an enlarged caecum and colon, relatively simple "
        "stomach, and continuously growing (hypsodont) cheek teeth in grazers.",
        55, "Paleocene",
    ),
    "Equidae": (
        "Horses, asses and zebras: a single functional hoofed toe per foot (side toes "
        "reduced to splint bones), very long limbs with a passive stay apparatus for "
        "standing/sleeping, high-crowned grinding teeth, and long-distance running.",
        55, "Eocene",
    ),
    "Ceratomorpha": (
        "The tapir + rhinoceros branch of odd-toed ungulates; ancestrally with four "
        "toes on the forefoot and three on the hind, and a tendency toward large body "
        "size and browsing.",
        50, "Eocene",
    ),
    "Tapiridae": (
        "Tapirs: pig-like browsers with a short prehensile proboscis formed from the "
        "nose and upper lip, four toes in front and three behind, a stocky body for "
        "pushing through forest, and striped-and-spotted young.",
        25, "Oligocene",
    ),
    "Rhinocerotidae": (
        "Rhinoceroses: massive herbivores with one or two keratin horns (no bony core) "
        "on the midline of the snout, thick protective skin, three toes per foot, "
        "columnar legs, and poor eyesight offset by acute hearing and smell.",
        30, "Oligocene",
    ),
    "Artiodactyla": (
        "Even-toed ungulates: weight borne equally on the third and fourth toes, a "
        "distinctive 'double-pulley' astragalus (ankle bone) allowing a very flexible "
        "foot; includes pigs, camels, ruminants, hippos and - nested within - the "
        "cetaceans.",
        65, "Paleocene",
    ),
    "Camelidae": (
        "Camels, llamas and relatives: two toes on broad padded feet (not true hooves), "
        "a pacing gait, oval nucleated red blood cells, a three-chambered ruminating "
        "stomach, splayed upper lip, and fat stored in humps or the body.",
        45, "Eocene",
    ),
    "Suina": (
        "Pigs and peccaries: non-ruminant omnivores with a simple stomach, a mobile "
        "cartilage-reinforced snout disc for rooting, bunodont (low, rounded-cusped) "
        "molars, continuously growing canine tusks, and four toes with the outer two "
        "not reaching the ground.",
        37, "Eocene",
    ),
    "Cetruminantia": (
        "Ruminants together with the hippo + whale clade (Whippomorpha); a molecular "
        "grouping within even-toed ungulates.",
        60, "Paleocene",
    ),
    "Ruminantia": (
        "Cud-chewing artiodactyls with a four-chambered stomach (rumen, reticulum, "
        "omasum, abomasum) and foregut microbial fermentation, no upper incisors (a "
        "horny dental pad instead), and usually bony horns or antlers; deer, cattle, "
        "antelope, giraffes.",
        50, "Eocene",
    ),
    "Whippomorpha": (
        "Hippopotamuses plus cetaceans (whales, dolphins): the closest living relatives "
        "of whales among land mammals; shared traits include hairlessness, aquatic or "
        "semi-aquatic habits, giving birth and suckling in water, and loss of sebaceous "
        "(sweat) glands.",
        54, "Eocene",
    ),
    "Hippopotamidae": (
        "Hippos: huge barrel-bodied semi-aquatic artiodactyls with eyes, ears and "
        "nostrils on top of the head, webbed toes, a near-hairless skin secreting a red "
        "sunscreen fluid, enlarged tusk-like canines and incisors, and a three-chambered "
        "non-ruminating stomach.",
        12, "Miocene",
    ),
    "Cetacea": (
        "Fully aquatic artiodactyls: a hairless streamlined body, forelimbs as flippers "
        "and no external hindlimbs, a horizontal tail fluke, a blowhole on top of the "
        "skull with telescoped facial bones, blubber, and nursing underwater.",
        38, "Eocene",
    ),
    "Mysticeti": (
        "Baleen whales: keratin baleen plates hanging from the upper jaw to filter "
        "small prey from water, paired blowholes, a symmetrical skull, no teeth as "
        "adults, and the largest body sizes of any animal.",
        28, "Oligocene",
    ),
    "Odontoceti": (
        "Toothed whales, dolphins and porpoises: a single blowhole, an asymmetrical "
        "skull, homodont conical teeth (or few), and biosonar produced by nasal air "
        "sacs and focused through a fatty forehead 'melon'.",
        34, "Oligocene",
    ),

    # ---- Euarchontoglires (non-primate) ----
    "Euarchontoglires": (
        "The placental clade of primates, treeshrews and colugos (Euarchonta) plus "
        "rodents and rabbits (Glires); mostly a molecular grouping, ancestrally small "
        "and arboreal.",
        75, "Cretaceous (Late)",
    ),
    "Glires": (
        "Rodents plus lagomorphs: a pair of ever-growing, self-sharpening chisel-like "
        "incisors in each jaw, no canines, and a wide toothless gap (diastema) before "
        "the cheek teeth, with the jaw able to slide forward to gnaw or back to chew.",
        68, "Paleocene",
    ),
    "Rodentia": (
        "The most species-rich mammal order: one pair of continuously growing incisors "
        "per jaw backed by hard enamel only on the front, powerful specialised jaw "
        "muscles (masseter) threaded through the skull, a diastema, and generally small "
        "size and high fecundity.",
        60, "Paleocene",
    ),
    "Lagomorpha": (
        "Rabbits, hares and pikas: a second small peg-like pair of upper incisors "
        "directly behind the first, a herbivorous hindgut-fermenting diet with "
        "re-ingestion of soft faeces (caecotrophy), a fenestrated (lattice-like) skull, "
        "and side-to-side chewing.",
        48, "Eocene",
    ),
    "Euarchonta": (
        "Primates together with treeshrews and (in some analyses) colugos; ancestrally "
        "small arboreal mammals with grasping feet and an emphasis on vision.",
        72, "Cretaceous (Late)",
    ),
    "Scandentia": (
        "Treeshrews: small squirrel-like Southeast Asian mammals with a long snout, "
        "sharp insectivore teeth, claws (not nails), a large brain-to-body ratio, and "
        "the highest metabolic rate relative to size of any mammal; 'absentee' parental "
        "care.",
        30, "Oligocene",
    ),

    # ---- Primates ----
    "Primates": (
        "Mammals with grasping hands and feet bearing flat nails and an opposable "
        "thumb/big toe, sensitive friction-ridged pads, forward-facing eyes in bony "
        "orbits giving stereoscopic vision, a reduced sense of smell, a large brain, "
        "and few, slow-developing offspring.",
        74, "Cretaceous (Late)",
    ),
    "Strepsirrhini": (
        "'Wet-nosed' primates - lemurs, lorises, galagos: a moist rhinarium and split "
        "upper lip tethered to the gum, a reflective tapetum lucidum for night vision, a "
        "tooth-comb of procumbent lower front teeth for grooming, and a grooming claw on "
        "the second toe.",
        60, "Paleocene",
    ),
    "Lemuriformes": (
        "Strepsirrhines that reached Madagascar and radiated there in isolation: a "
        "tooth-comb, a grooming claw, scent-marking, often female social dominance, and "
        "body forms from mouse-sized to (extinct) gorilla-sized.",
        40, "Eocene",
    ),
    "Lorisiformes": (
        "Slow-climbing nocturnal strepsirrhines of Africa and Asia: a very slow "
        "deliberate hand-over-hand gait (lorises) or leaping (galagos), a powerful "
        "grasp with a reduced index finger, a tooth-comb, and a retia mirabilia in the "
        "limbs that resists fatigue.",
        38, "Eocene",
    ),
    "Haplorhini": (
        "'Dry-nosed' primates - tarsiers, monkeys and apes: no rhinarium and a mobile "
        "continuous upper lip, no tapetum, a retinal fovea for sharp central vision, a "
        "single-chambered uterus, a haemochorial placenta, and an inability to make "
        "their own vitamin C.",
        65, "Paleocene",
    ),
    "Tarsiiformes": (
        "Tiny nocturnal Southeast Asian haplorhines: enormous immobile eyes (each about "
        "as large as the brain) in a neck that rotates ~180 deg, elongated tarsal "
        "(ankle) bones for prodigious leaping, entirely carnivorous diet, and long "
        "grasping fingers with rounded pads.",
        20, "Miocene",
    ),
    "Simiiformes": (
        "Monkeys and apes (anthropoids): a fused frontal bone and lower-jaw symphysis, "
        "a bony back wall to the eye socket, dry nose, forward fovea and full colour "
        "vision in many, larger brains, and generally diurnal, social life.",
        43, "Eocene",
    ),
    "Platyrrhini": (
        "New World monkeys: side-facing nostrils set wide apart, three premolars per "
        "quadrant, an ear region without a bony tube, exclusively arboreal, many with a "
        "prehensile tail; the only anthropoids that colonised the Americas.",
        25, "Oligocene",
    ),
    "Callitrichidae": (
        "Marmosets and tamarins: the smallest anthropoids, with claw-like nails on all "
        "digits except the big toe, usually twin births, cooperative care by the group, "
        "and (in marmosets) chisel teeth for gouging tree bark to feed on gum.",
        18, "Miocene",
    ),
    "Cebidae": (
        "New World monkeys comprising capuchins and squirrel monkeys (plus the "
        "callitrichids in broad usage): agile, large-brained, highly manipulative "
        "omnivores; capuchins have a weakly prehensile tail, squirrel monkeys a "
        "non-prehensile one.",
        20, "Miocene",
    ),
    "Cebinae": (
        "Stocky, exceptionally large-brained New World monkeys with a semi-prehensile "
        "tail carried coiled, strong hands, extractive foraging, documented tool use "
        "(stone hammers, anvils) and fur-rubbing behaviour.",
        7, "Miocene",
    ),
    "Saimiriinae": (
        "Small slender cebids with a long non-prehensile tail used for balance, a short "
        "close 'gothic arch' of white facial fur around dark muzzle and eyes, very large "
        "brain relative to body, and large mixed-sex troops.",
        2, "Pleistocene",
    ),
    "Atelidae": (
        "The largest New World monkeys - howlers, spider, woolly and muriqui monkeys - "
        "all with a strongly prehensile tail bearing a naked, friction-ridged gripping "
        "pad on its underside, used as a fifth limb.",
        18, "Miocene",
    ),
    "Alouattinae": (
        "Bulky folivorous atelids with an enlarged hyoid bone forming a resonating "
        "throat chamber that produces roaring calls audible for kilometres; a "
        "prehensile tail; a sluggish, energy-conserving lifestyle; some have routine "
        "trichromatic colour vision.",
        6, "Miocene",
    ),
    "Atelinae": (
        "Long-limbed acrobatic atelids with a hook-like hand whose thumb is reduced or "
        "absent (aiding brachiation), a highly prehensile tail, a fruit-heavy diet, and "
        "fission-fusion social groups.",
        3, "Pliocene",
    ),
    "Aotidae": (
        "Night (owl) monkeys - the only nocturnal anthropoids: huge brown eyes with no "
        "fovea and a monochromatic retina, a non-prehensile tail, monogamous pairs with "
        "heavy paternal carrying of infants, and scent communication.",
        4, "Pliocene",
    ),
    "Pitheciidae": (
        "Titis, sakis and uakaris: seed-predator ('sclerocarnivore') New World monkeys "
        "with splayed, procumbent lower canines and robust premolars for cracking hard "
        "unripe fruit and seeds; a non-prehensile, often bushy tail.",
        18, "Miocene",
    ),
    "Callicebinae": (
        "Titi monkeys: small monogamous pitheciids that sleep and sit with tails "
        "entwined, defend territories with dawn duets, show intense male infant care, "
        "and eat mostly fruit supplemented with leaves.",
        6, "Miocene",
    ),
    "Pitheciinae": (
        "Sakis, bearded sakis and uakaris: seed-predator New World monkeys with "
        "splayed, forward-tilted lower canines and thick enamel for prying open and "
        "cracking hard unripe fruit and seeds; a non-prehensile, often bushy tail; "
        "agile trunk-to-trunk leaping.",
        14, "Miocene",
    ),
    "Catarrhini": (
        "Old World monkeys and apes: narrow downward-facing nostrils close together, "
        "two premolars per quadrant, a bony ear tube (tubular ectotympanic), routine "
        "trichromatic colour vision, and no prehensile tail.",
        30, "Oligocene",
    ),
    "Cercopithecidae": (
        "Old World monkeys: bilophodont molars (paired transverse ridges), sitting pads "
        "of hardened skin (ischial callosities), often cheek pouches for storing food, "
        "a tail that is never prehensile, and narrow chests with limbs built for "
        "quadrupedal walking.",
        18, "Miocene",
    ),
    "Cercopithecinae": (
        "The cheek-pouched Old World monkeys - macaques, baboons, mangabeys, guenons, "
        "vervets: large distensible cheek pouches, a simple stomach, a more omnivorous "
        "diet, and often terrestrial, large-group living with pronounced male-biased "
        "size.",
        12, "Miocene",
    ),
    "Colobinae": (
        "Leaf-eating Old World monkeys - colobus, langurs, proboscis and snub-nosed "
        "monkeys: a large multi-chambered ('ruminant-like') foregut-fermenting stomach, "
        "high-crested shearing molars, reduced or absent thumb in colobus, and long "
        "tails and limbs for leaping.",
        11, "Miocene",
    ),
    "Hominoidea": (
        "Apes: no external tail, a broad flat chest with the shoulder blades on the "
        "back, very mobile shoulder and wrist joints (from an ancestry of arm-hanging), "
        "a shortened lumbar spine, an appendix, larger brains, and Y-5 molar cusp "
        "patterns.",
        20, "Miocene",
    ),
    "Hylobatidae": (
        "Gibbons ('lesser apes'): small, slender, monogamous apes that brachiate "
        "beneath branches with extremely long arms and hook grips at high speed, sing "
        "loud territorial duets, and have 44 chromosomes (unusually variable across "
        "genera).",
        8, "Miocene",
    ),
    "Hominidae": (
        "Great apes and humans: large bodies and brains, no tail, broad flat faces, "
        "prolonged childhood and lifespan, complex problem-solving and tool use, and a "
        "shoulder/torso built for both climbing and (in some) suspensory or upright "
        "postures.",
        17, "Miocene",
    ),
    "Ponginae": (
        "Orangutans: the only exclusively Asian great apes and the most arboreal, "
        "moving by cautious four-handed climbing; pronounced sexual dimorphism with "
        "flanged adult males; very long inter-birth intervals; largely solitary; a "
        "fruit-tracking mental map of the forest.",
        4, "Pliocene",
    ),
    "Homininae": (
        "African great apes and humans: gorillas, chimpanzees, bonobos and humans; "
        "shared cranial and dental features and knuckle-walking ancestry (retained by "
        "gorillas and chimps), from which the human bipedal lineage diverged.",
        10, "Miocene",
    ),
    "Gorillini": (
        "Gorillas: the largest living primates, ground-dwelling knuckle-walkers with "
        "extreme male size and a sagittal skull crest, a folivorous hindgut-fermenting "
        "diet, cohesive one-male ('silverback') groups, and 48 chromosomes.",
        2, "Pleistocene",
    ),
    "Hominini": (
        "Chimpanzees and bonobos together with humans and their extinct bipedal "
        "relatives (australopiths, Homo); the branch on which habitual terrestrial "
        "bipedalism, reduced canines and, later, large brains evolved.",
        7, "Miocene",
    ),
    "Panina": (
        "The genus Pan - chimpanzees and bonobos: knuckle-walking African apes with "
        "fission-fusion societies, tool use, hunting and food sharing, a swollen "
        "sexual skin in females, and ~98.8% genome identity with humans.",
        2, "Pleistocene",
    ),
    "Hominina": (
        "The human branch after the split from Pan: habitual upright bipedal walking "
        "(a forward foramen magnum, S-curved spine, bowl-shaped pelvis, arched "
        "non-grasping foot, valgus knee), small canines, and later a greatly enlarged "
        "brain, language and cumulative culture.",
        4, "Pliocene",
    ),
    "Pan troglodytes": (
        "Pan troglodytes: the more widespread, northern species of Pan, living in "
        "male-bonded communities with lethal territorial aggression, extensive tool "
        "kits (termite-fishing, nut-cracking), cooperative hunting of monkeys, and "
        "regional behavioural 'cultures'.",
        1, "Pleistocene",
    ),
    "Pan paniscus": (
        "Pan paniscus: the southern species of Pan, restricted to forests south of the "
        "Congo River; more gracile, female-centred and egalitarian, using frequent "
        "socio-sexual contact to defuse tension, with little lethal aggression.",
        0.5, "Pleistocene",
    ),

    # ---- land plants ----
    "Charophyta": (
        "The freshwater green algae most closely related to land plants (e.g. "
        "Zygnematophyceae, Charophyceae, Coleochaetophyceae); phragmoplast cell "
        "division, plasmodesmata and rosette cellulose synthases in some - features "
        "inherited by land plants. A paraphyletic grade.",
        850, "Neoproterozoic",
    ),
    "Plantae": (
        "Land plants (embryophytes): a multicellular diploid embryo retained and "
        "nourished on the parent (hence 'embryophyte'), alternation of generations with "
        "a sporophyte, a waxy cuticle with stomata, sporopollenin-walled spores, and "
        "sex organs (archegonia and antheridia) with a protective jacket of cells.",
        500, "Cambrian",
    ),
    "Bryophyta": (
        "Non-vascular land plants - mosses, liverworts, hornworts: a dominant "
        "photosynthetic gametophyte with a small, unbranched, nutritionally dependent "
        "sporophyte bearing a single sporangium; no true xylem/phloem, roots or leaves; "
        "swimming sperm needing a film of water.",
        490, "Cambrian",
    ),
    "Bryopsida": (
        "Bryophytes with spirally arranged one-cell-thick leaves on a radial stem, "
        "rhizoids for anchorage, an elaborate spore capsule with a toothed peristome and "
        "operculum for gradual spore release, and conducting cells (hydroids/leptoids).",
        410, "Devonian",
    ),
    "Marchantiophyta": (
        "Bryophytes that are either flat dorsiventral thalli or leafy shoots with leaves "
        "in three ranks (the underside row reduced); oil bodies in the cells; a "
        "capsule that splits into four valves; no stomata (thalloid forms have air pores).",
        420, "Silurian",
    ),
    "Anthocerotophyta": (
        "Bryophytes with a thin thallus whose cells often each contain a single large "
        "chloroplast with a pyrenoid (a carbon-concentrating feature unique among land "
        "plants), and a needle-like sporophyte that grows continuously from a basal "
        "meristem and splits lengthwise.",
        300, "Carboniferous",
    ),
    "Tracheophyta": (
        "Vascular plants: lignified water-conducting xylem (tracheids/vessels) and "
        "sugar-conducting phloem, a dominant branched sporophyte with true roots and "
        "(usually) leaves, and stomatal control of gas exchange.",
        425, "Silurian",
    ),
    "Lycopodiophyta": (
        "The oldest living vascular-plant lineage - clubmosses, spikemosses, quillworts: "
        "small single-veined leaves (microphylls), sporangia borne singly on the upper "
        "leaf surface (often in cones), and roots that branch by equal forking; "
        "Carboniferous tree forms built the coal swamps.",
        400, "Devonian",
    ),
    "Lycopodiales": (
        "Homosporous clubmosses (Lycopodium and relatives): trailing or erect stems "
        "clothed in small microphylls, upright spore cones, a long-lived underground "
        "gametophyte fed by fungi, and spores once sold as flash powder.",
        250, "Triassic",
    ),
    "Isoetales": (
        "Quillworts (Isoetes): a squat corm-like stem bearing a rosette of grass-like "
        "quill leaves, each with a sporangium sunk in its swollen base; heterosporous; "
        "CAM photosynthesis in aquatic species; the last survivors of the giant "
        "lycopod (Lepidodendron) lineage.",
        130, "Cretaceous (Early)",
    ),
    "Selaginellales": (
        "Spikemosses (Selaginella): creeping stems with four ranks of microphylls each "
        "bearing a tiny flap (ligule), heterospory (two spore sizes), roots on leafless "
        "branchlets (rhizophores), and desiccation tolerance in the 'resurrection "
        "plants'.",
        300, "Carboniferous",
    ),
    "Euphyllophyta": (
        "Vascular plants with true megaphyll leaves (a branched vein system, from "
        "flattened and webbed branch systems), sporangia in clusters, and a distinctive "
        "small loop (pseudoendospory) in early xylem; ferns plus seed plants.",
        415, "Devonian",
    ),
    "Polypodiopsida": (
        "Monilophytes: vascular spore plants with megaphylls that unroll from a coiled "
        "fiddlehead (circinate vernation), sporangia usually grouped in sori on the leaf "
        "underside, a free-living heart-shaped gametophyte, and swimming sperm.",
        385, "Devonian",
    ),
    "Polypodiidae": (
        "Leptosporangiate ferns - ~90% of living fern species: each sporangium develops "
        "from a single cell and has a spring-loaded annulus that catapults the spores; "
        "many diversified in the shade of angiosperm forests in the Cretaceous.",
        360, "Carboniferous",
    ),
    "Marattiidae": (
        "Eusporangiate marattioid ferns: large tropical plants with massive fleshy "
        "fronds, swollen starchy stipule-buttressed bases, sporangia fused into "
        "synangia, and a long-lived fleshy gametophyte; relicts of a Carboniferous "
        "tree-fern lineage.",
        175, "Jurassic",
    ),
    "Equisetidae": (
        "Horsetails (Equisetum): jointed, hollow, silica-impregnated ('scouring rush') "
        "stems with whorls of tiny fused scale leaves and whorled branches, spores borne "
        "on umbrella-shaped sporangiophores in a terminal cone, and spores with "
        "moisture-sensitive coiling straps (elaters).",
        130, "Cretaceous (Early)",
    ),
    "Ophioglossidae": (
        "Whisk ferns (Psilotum) and adder's-tongue ferns (Ophioglossum): Psilotum has "
        "no true roots or leaves and dichotomously forking green stems with three-lobed "
        "synangia; Ophioglossum bears a single fertile spike and holds the record for "
        "chromosome number.",
        270, "Permian",
    ),
    "Spermatophyta": (
        "Seed plants: reproduction by seeds (a dormant embryo packaged with food and a "
        "protective coat), pollen carrying the male gametes so no water is needed for "
        "fertilisation, a much-reduced gametophyte kept inside the parent, ovules, and "
        "wood from a bifacial cambium in most.",
        340, "Carboniferous",
    ),
    "Acrogymnospermae": (
        "Seed plants whose ovules and seeds sit exposed on the surface of a scale or "
        "leaf ('naked seeds'), not enclosed in a fruit; wind pollination with a "
        "pollination droplet; mostly woody; simple tracheid-only xylem in conifers.",
        320, "Carboniferous",
    ),
    "Pinophyta": (
        "Cone-bearing gymnosperms: mostly evergreen trees with needle or scale leaves, "
        "resin canals, wood of tracheids with bordered pits, seeds on woody cone scales "
        "(or in a fleshy aril), and dominance of cold and dry forests.",
        290, "Permian",
    ),
    "Cycadophyta": (
        "Palm-like gymnosperms with a stout unbranched trunk, a crown of tough pinnate "
        "leaves, coralloid roots housing nitrogen-fixing cyanobacteria, huge cones, "
        "motile (swimming) sperm, and dioecy; living genera radiated only in the last "
        "~12 million years.",
        250, "Triassic",
    ),
    "Ginkgophyta": (
        "A single living species, Ginkgo biloba: a tree with fan-shaped, forked-veined "
        "deciduous leaves, short spur shoots, swimming sperm, and fleshy foul-smelling "
        "seed coats; unchanged in form for ~200 million years - a 'living fossil'.",
        170, "Jurassic",
    ),
    "Gnetophyta": (
        "An odd gymnosperm group of three very different genera - Ephedra (jointed "
        "desert shrubs), Gnetum (broadleaf tropical vines/trees) and Welwitschia (two "
        "ever-growing strap leaves): vessel elements in the xylem and flower-like "
        "compound cones, features convergent with angiosperms.",
        120, "Cretaceous (Early)",
    ),
    "Angiosperms": (
        "Flowering plants: ovules enclosed in a carpel that ripens into a fruit, "
        "flowers, double fertilisation producing a nutritive triploid endosperm, "
        "vessels in the xylem, sieve-tube/companion-cell phloem, and a very reduced "
        "gametophyte (an 8-nucleate embryo sac).",
        195, "Jurassic",
    ),
    "Mesangiospermae": (
        "The 'core' flowering plants (~99.9% of species) - monocots, eudicots, "
        "magnoliids, Chloranthales and Ceratophyllales - diverging from each other in a "
        "rapid burst in the Early Cretaceous.",
        150, "Cretaceous (Early)",
    ),
    "Magnoliids": (
        "Core angiosperms that are neither monocots nor eudicots: mostly aromatic woody "
        "plants (magnolias, laurels, nutmeg, black pepper, avocado) with flower parts "
        "in threes, pollen with a single aperture, and often beetle pollination.",
        130, "Cretaceous (Early)",
    ),
    "Chloranthales": (
        "A small early-diverging angiosperm lineage (Chloranthaceae) of aromatic herbs "
        "and shrubs with swollen leaf nodes, toothed opposite leaves, and tiny reduced "
        "flowers; abundant in the Early Cretaceous pollen record.",
        100, "Cretaceous (Late)",
    ),
    "CME": (
        "The clade uniting Ceratophyllales with the monocots and eudicots - i.e. most "
        "flowering-plant species; a molecular grouping within the core angiosperms.",
        140, "Cretaceous (Early)",
    ),
    "Ceratophyllales": (
        "Hornworts of the pond (Ceratophyllum): rootless submerged aquatic plants with "
        "whorls of brittle forked leaves, water pollination, and one of the oldest "
        "angiosperm fossil records; sister to the eudicots in many analyses.",
        45, "Eocene",
    ),
    "Monocots": (
        "Flowering plants with a single seed leaf (cotyledon), leaves with parallel "
        "veins and sheathing bases, flower parts in threes, pollen with one aperture, "
        "scattered vascular bundles with no cambium (so rarely truly woody), and a "
        "fibrous root system.",
        130, "Cretaceous (Early)",
    ),
    "Poaceae": (
        "Grasses (Poaceae): hollow jointed stems (culms), two-ranked leaves with a "
        "split sheath and a small ligule, wind-pollinated flowers reduced to florets in "
        "spikelets, a single-seeded grain (caryopsis), silica bodies, and growth from "
        "the leaf base so they regrow after grazing or fire.",
        75, "Cretaceous (Late)",
    ),
    "Liliales": (
        "Monocots (Liliales and lily-like relatives) with showy flowers in threes, "
        "often six tepals and six stamens, a superior ovary, bulbs or corms, and "
        "typically nectar- and pollen-rewarding insect pollination.",
        110, "Cretaceous (Late)",
    ),
    "Orchidaceae": (
        "The largest plant family (Orchidaceae): bilaterally symmetric flowers with a "
        "landing-pad lip (labellum), stamens and style fused into a column, pollen in "
        "sticky masses (pollinia), dust-like seeds with no endosperm needing fungal "
        "partners to germinate, and CAM or epiphytic habits in many.",
        85, "Cretaceous (Late)",
    ),
    "Eudicots": (
        "Flowering plants with pollen having three apertures (tricolpate) - a trait "
        "with a sharp ~125-million-year-old fossil first appearance; usually two seed "
        "leaves, net-veined leaves, flower parts in fours or fives, a taproot, and a "
        "vascular cambium giving true wood.",
        125, "Cretaceous (Early)",
    ),
    "Rosids": (
        "One of the two big eudicot clades (~25% of angiosperms): often woody, with "
        "flowers whose petals are separate, many stamens, and a tendency to nitrogen-"
        "fixing root symbioses; includes legumes, roses, oaks, mustards, mallows, "
        "eucalypts.",
        115, "Cretaceous (Early)",
    ),
    "Vitales": (
        "A single family (Vitaceae) - grapes and Virginia creeper: climbing shrubs "
        "with leaf-opposed tendrils, swollen leaf-base nodes, small four/five-parted "
        "flowers with a nectar disc, and a berry fruit; sister to the rest of the rosids.",
        70, "Cretaceous (Late)",
    ),
    "Eurosids": (
        "The core of the rosid radiation, split into the fabids and malvids; a rapid "
        "Cretaceous diversification producing most rosid families.",
        110, "Cretaceous (Early)",
    ),
    "Fabids": (
        "The fabid (eurosid I / nitrogen-fixing) clade: legumes, roses, figs, oaks, "
        "willows, cucurbits, spurges; contains almost all plants able to form root "
        "nodules with nitrogen-fixing bacteria (the 'nitrogen-fixing clade').",
        105, "Cretaceous (Late)",
    ),
    "Malvids": (
        "The malvid (eurosid II) clade: mallows and cotton, mustards and capers, "
        "citrus, myrtles and eucalypts, sumac and cashew; many produce glucosinolate "
        "or terpene chemical defences.",
        102, "Cretaceous (Late)",
    ),
    "Asterids": (
        "The other big eudicot clade (~1/3 of angiosperms): usually with petals fused "
        "into a tube, a fixed low number of stamens attached to the corolla, ovules "
        "with a single integument and a thin nucellus, and iridoid or alkaloid "
        "chemistry; heathers, coffee, nightshades, mints, sunflowers.",
        112, "Cretaceous (Early)",
    ),
    "Euasterids": (
        "The core asterids (lamiids + campanulids): sympetalous flowers with the "
        "stamens alternating with the corolla lobes, and a strong tendency to fuse "
        "flower parts and reduce their number.",
        105, "Cretaceous (Late)",
    ),
    "Campanulids": (
        "The campanulid (euasterid II) clade: bellflowers, sunflowers and the whole "
        "daisy family, hollies, ivies, carrots; often with inferior ovaries and "
        "early-fusing ('early sympetaly') corollas.",
        98, "Cretaceous (Late)",
    ),
    "Lamiids": (
        "The lamiid (euasterid I) clade: mints, nightshades (tomato, potato), coffee "
        "and gentians, borages, olives; usually opposite leaves, corollas that fuse "
        "late, and often a two-carpel ovary and specialised alkaloids.",
        100, "Cretaceous (Late)",
    ),

    # ---- Fungi ----
    "Fungi": (
        "Osmotrophic eukaryotes that digest food externally with secreted enzymes and "
        "absorb the products; cell walls containing chitin; glycogen as storage; a "
        "haploid-dominant life cycle; no plastids or phagotrophy in most; includes "
        "highly reduced parasites at its base.",
        1050, "Mesoproterozoic",
    ),
    "Rozellomycota": (
        "The earliest-branching fungi - rozellids (Cryptomycota) and Microsporidia: "
        "extreme intracellular parasites, mostly without a chitin wall in the feeding "
        "stage; Microsporidia have among the smallest eukaryotic genomes, mitosomes "
        "instead of mitochondria, and infect hosts by firing a coiled polar tube.",
        700, "Neoproterozoic",
    ),
    "Aphelidiomycota": (
        "Aphelids: tiny intracellular parasites (parasitoids) of algae; a walled "
        "resting spore, an amoeboid or flagellate infective stage that enters the host "
        "and phagocytoses its contents from within, then fills the host cell with a "
        "plasmodium.",
        600, "Neoproterozoic",
    ),
    "Eumycota": (
        "The 'true fungi': a chitinous cell wall present throughout the life cycle, "
        "growth as absorptive hyphae or yeasts, and reproduction by non-motile spores "
        "(the flagellum is retained only in the basal chytrid lineages and lost above "
        "them).",
        900, "Neoproterozoic",
    ),
    "Chytridiomycota": (
        "Chytrids: the main fungi that keep a single posterior whiplash flagellum, on "
        "motile zoospores that swim to new substrates; mostly aquatic or soil "
        "saprotrophs and parasites; includes Batrachochytrium, the cause of global "
        "amphibian declines.",
        650, "Neoproterozoic",
    ),
    "Amastigomycota": (
        "The non-flagellated fungi (zygomycetes plus Dikarya): the flagellum and "
        "centriole are lost, so dispersal is entirely by non-motile spores carried on "
        "air or water or by animals.",
        700, "Neoproterozoic",
    ),
    "Zoopagomyceta": (
        "An early non-flagellated fungal clade of parasites and predators of small "
        "animals, amoebae and other fungi - e.g. Entomophthora, which manipulates and "
        "kills flies, and trap-forming predators of nematodes; often forcibly "
        "discharged spores.",
        550, "Cambrian",
    ),
    "Mucoromyceta": (
        "Fast-growing moulds with wide, largely septum-free (coenocytic) hyphae: "
        "sexual reproduction by a thick-walled zygospore where two hyphae fuse, and "
        "asexual spores made in a stalked sac (sporangium); bread mould Rhizopus; some "
        "form plant root symbioses.",
        560, "Cambrian",
    ),
    "Symbiomycota": (
        "The fungi defined by ancient plant symbiosis: the arbuscular mycorrhizal "
        "Glomeromycota plus the Dikarya; ancestrally associated with land plants.",
        550, "Cambrian",
    ),
    "Glomeromycota": (
        "Arbuscular mycorrhizal fungi: obligate root symbionts of most land plants, "
        "growing tree-like feeding structures (arbuscules) inside root cortex cells; "
        "coenocytic hyphae, giant multinucleate spores, no known sexual stage; partners "
        "in the plant colonisation of land.",
        480, "Cambrian",
    ),
    "Dikarya": (
        "The 'higher fungi' (Ascomycota + Basidiomycota): a prolonged dikaryon stage "
        "with two distinct unfused haploid nuclei per cell, regularly septate hyphae "
        "with pored cross-walls, croziers or clamp connections at cell division, and "
        "large complex fruiting bodies.",
        560, "Cambrian",
    ),
    "Ascomycota": (
        "Sac fungi: sexual spores (classically eight) formed by meiosis inside a "
        "cylindrical sac, the ascus, and usually shot out; abundant asexual spores "
        "(conidia); the fungal partner of most lichens; yeasts, moulds (Penicillium, "
        "Aspergillus), morels, truffles.",
        530, "Cambrian",
    ),
    "Taphrinomycotina": (
        "An early-diverging, mostly simple ascomycete grade: no fruiting body; includes "
        "the fission yeast Schizosaccharomyces (a model organism), the plant pathogen "
        "Taphrina (peach leaf curl), and Pneumocystis, a cause of pneumonia in "
        "immunocompromised people.",
        450, "Ordovician",
    ),
    "Saccharomyceta": (
        "The great majority of Ascomycota: the budding yeasts (Saccharomyces - baking, "
        "brewing, biology) plus the Pezizomycotina, filamentous ascomycetes that build "
        "true fruiting bodies and include most lichen fungi, many plant pathogens, and "
        "the penicillin and cephalosporin producers.",
        450, "Ordovician",
    ),
    "Basidiomycota": (
        "Club fungi: sexual spores (usually four) budded externally on a club-shaped "
        "cell, the basidium, after meiosis; a long-lived dikaryotic mycelium often with "
        "clamp connections; complex fruiting bodies in many; mushrooms, bracket fungi, "
        "puffballs, rusts and smuts.",
        520, "Cambrian",
    ),
    "Pucciniomycotina": (
        "Mostly the rust fungi: obligate biotrophic plant parasites with the most "
        "complex life cycles known in fungi - up to five spore types and, in many, an "
        "obligatory alternation between two unrelated host plants; simple septal pores, "
        "no clamp connections.",
        450, "Ordovician",
    ),
    "Orthomycotina": (
        "The basidiomycete clade uniting the smut fungi (Ustilaginomycotina) with the "
        "mushroom-forming fungi (Agaricomycotina); a molecular grouping within "
        "Basidiomycota.",
        480, "Cambrian",
    ),
    "Agaricomycotina": (
        "The mushroom lineage: fungi that build large fleshy or woody fruiting bodies "
        "with the spore layer on gills, pores or teeth; the principal decomposers of "
        "wood, including the white-rot fungi that are the main organisms able to break "
        "down lignin; also many ectomycorrhizal partners.",
        430, "Silurian",
    ),
    "Ustilaginomycotina": (
        "Smut fungi: biotrophic parasites mainly of grasses and cereals that replace "
        "the host's flowers or grains with sooty masses of thick-walled teliospores; a "
        "dimorphic life cycle switching between a harmless yeast and an infectious "
        "filament; intracellular but not killing host cells.",
        380, "Devonian",
    ),

    # ---- Chromista / SAR ----
    "Chromista": (
        "A (probably non-monophyletic) grouping of algae and their relatives with "
        "red-algal-derived plastids inside four membranes or a periplastid compartment "
        "- diatoms, brown algae, dinoflagellates, cryptomonads, haptophytes - together "
        "with many secondarily non-photosynthetic lineages (ciliates, oomycetes, "
        "foraminifera).",
        1100, "Mesoproterozoic",
    ),
    "SAR": (
        "A major molecular clade - Stramenopiles (diatoms, brown algae, oomycetes), "
        "Alveolates (dinoflagellates, ciliates, apicomplexan parasites) and Rhizaria "
        "(foraminifera, radiolarians); no morphological synapomorphy, though many share "
        "plastids of red-algal secondary origin and tubular mitochondrial cristae.",
        1050, "Mesoproterozoic",
    ),
    "Hacrobia": (
        "A proposed (and much-disputed) grouping of haptophytes (coccolithophores) with "
        "cryptophytes and kin; if real, united only by molecular data - the two groups "
        "differ greatly in structure.",
        1000, "Mesoproterozoic",
    ),
}


# Corrections applied on top of AUTHORED, so that no clade is older than the
# clade that contains it (a child crown age must be younger than its parent's).
# These nudge a handful of early-Cenozoic and basal-animal nodes into a
# consistent ladder; all still within the published uncertainty ranges.
_ADJUST = {
    "Metazoa": (700, "Neoproterozoic (Cryogenian)"),
    "Porifera": (690, "Neoproterozoic (Cryogenian)"),
    "Demospongiae": (640, "Neoproterozoic (Cryogenian)"),
    "Eumetazoa": (635, "Neoproterozoic (Ediacaran)"),
    "ParaHoxozoa": (615, "Neoproterozoic (Ediacaran)"),
    "Symbiomycota": (565, "Cambrian"),
    "CAM": (1570, "Mesoproterozoic"),
    "Eutheria": (84, "Cretaceous (Late)"),
    "Atlantogenata": (80, "Cretaceous (Late)"),
    "Afrotheria": (77, "Cretaceous (Late)"),
    "Boreoeutheria": (81, "Cretaceous (Late)"),
    "Euarchontoglires": (78, "Cretaceous (Late)"),
    "Laurasiatheria": (79, "Cretaceous (Late)"),
    "Eulipotyphla": (72, "Cretaceous (Late)"),
    "Scrotifera": (77, "Cretaceous (Late)"),
    "Ferungulata": (75, "Cretaceous (Late)"),
    "Euungulata": (74, "Cretaceous (Late)"),
    "Euarchonta": (76, "Cretaceous (Late)"),
    "Glires": (66, "Paleocene"),
}


def children_of(tree, name):
    return sorted(k for k, v in tree.items() if v.get("parent") == name)


def descendants(tree, root):
    """`root` and everything below it."""
    out, stack = set(), [root]
    while stack:
        n = stack.pop()
        if n in out:
            continue
        out.add(n)
        stack.extend(children_of(tree, n))
    return out


def main():
    with open(TREE, encoding="utf-8") as fh:
        tree = json.load(fh)

    missing = [c for c in AUTHORED if c not in tree]
    if missing:
        raise SystemExit(f"authored clades not in tree_of_life.json: {missing}")

    tag_members = {tag: descendants(tree, root) for root, tag in TAG_ROOTS.items() if root in tree}

    rows = []
    for clade in sorted(tree):
        traits, mya, geo = AUTHORED.get(clade, ("", "", ""))
        if clade in _ADJUST:
            mya, geo = _ADJUST[clade]
        tags = sorted(tag for tag, members in tag_members.items() if clade in members)
        rows.append({
            "Clade": clade,
            "Parent": tree[clade].get("parent") or "",
            "Children": ", ".join(children_of(tree, clade)),
            "Traits": traits,
            "DivergenceMya": str(mya) if mya != "" else "",
            "GeoTime": geo,
            "Tags": " ".join(tags),
        })

    by_clade = {r["Clade"]: r for r in rows}
    for r in rows:
        p = by_clade.get(r["Parent"])
        if p and r["DivergenceMya"] and p["DivergenceMya"]:
            if float(r["DivergenceMya"]) > float(p["DivergenceMya"]):
                print(f"  WARNING: {r['Clade']} ({r['DivergenceMya']}) older than parent "
                      f"{p['Clade']} ({p['DivergenceMya']}) -- add an _ADJUST entry")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(FIELDS + ["Tags"])
        for r in rows:
            w.writerow([r[f] for f in FIELDS] + [r["Tags"]])

    print(f"wrote {OUT}: {len(rows)} clades")


if __name__ == "__main__":
    main()
