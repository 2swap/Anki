# Geography deck: boundary data sources

Most `Data/*/geog_*.js` files predate this list and their sources weren't
recorded. Subdivision data added or replaced since 2026-10-01:

| File | Features | Source | License |
|---|---|---|---|
| `Data/Indonesia/geog_Indonesia.js` | 38 provinces (as of 2022) | Badan Informasi Geospasial boundaries (13 Jun 2023), via [Alf-Anas/batas-administrasi-indonesia](https://github.com/Alf-Anas/batas-administrasi-indonesia) | Indonesian government data |
| `Data/Ethiopia/geog_Ethiopia.js` | 12 regional states + 2 chartered cities (as of 2023) | © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, fetched 2026-10-01 | ODbL 1.0 |
| `Data/Russia/geog_Russia.js` (federal subjects) | 83 federal subjects, internationally recognised borders | Geometry: [geoBoundaries](https://www.geoboundaries.org/) RUS ADM1 (from OpenStreetMap); names: © OpenStreetMap contributors | ODbL 1.0 |
| `Data/{Chile,India,Philippines,Egypt,Pakistan,Malaysia}/geog_*.js` (regions) | Chile 16 regions, India 36 states/UTs, Philippines 82 provinces + Metro Manila, Egypt 27 governorates, Pakistan 7 units, Malaysia 13 states + 3 federal territories | © OpenStreetMap contributors, fetched 2026-10-01; coastal ones clipped to [Natural Earth](https://www.naturalearthdata.com/) 1:10m land (OSM areas there include territorial waters) | ODbL 1.0 (Natural Earth: public domain) |
| `bluemarble/` (built by `build_tiles.py`) | Basemap imagery | NASA Earth Observatory, Blue Marble Next Generation (July 2004, topography + bathymetry) | Public domain |

All boundary geometry above was simplified (to roughly 300–500 m) and tiny
islets were dropped to keep the files small enough for flashcards.
