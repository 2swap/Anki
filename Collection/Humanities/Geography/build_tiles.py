"""Cut NASA's Blue Marble into the Geography deck's globe basemap + tiles.

Run by hand once (it downloads ~27 MB), from anywhere:  python Geography/build_tiles.py

Source: Blue Marble Next Generation, July 2004, with topography and bathymetry,
21600x10800 equirectangular (about 1.9 km per pixel), public domain, from
NASA Earth Observatory. Writes, under Geography/bluemarble/ (git-ignored;
rerun this script to recreate it):

    src/<source>.jpg               the download, kept so reruns are offline
    geog_bluemarble.jpg            4096x2048 whole-globe basemap (zoomed out)
    tiles/geog_bm_<col>_<row>.jpg  36 x 18 tiles of 10 x 10 degrees, 600x600 px;
                                   col 0 starts at 180°W, row 0 at 90°N

geog.js draws the basemap on the globe and lays the tiles over it once you
zoom in. build.py adds all of them to manifest.json's media.
"""

import os
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bluemarble")
SRC_URL = ("https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73751/"
           "world.topo.bathy.200407.3x21600x10800.jpg")
SRC = os.path.join(OUT, "src", os.path.basename(SRC_URL))
TILE_DEG = 10
BASE_SIZE = (4096, 2048)

Image.MAX_IMAGE_PIXELS = None  # the source is 233 megapixels


def main():
    os.makedirs(os.path.dirname(SRC), exist_ok=True)
    if not os.path.exists(SRC):
        print(f"downloading {SRC_URL}")
        urllib.request.urlretrieve(SRC_URL, SRC + ".part")
        os.replace(SRC + ".part", SRC)
    img = Image.open(SRC).convert("RGB")
    w, h = img.size
    cols, rows = 360 // TILE_DEG, 180 // TILE_DEG
    tw, th = w // cols, h // rows

    img.resize(BASE_SIZE, Image.LANCZOS).save(
        os.path.join(OUT, "geog_bluemarble.jpg"), quality=88)

    tile_dir = os.path.join(OUT, "tiles")
    os.makedirs(tile_dir, exist_ok=True)
    for row in range(rows):
        for col in range(cols):
            tile = img.crop((col * tw, row * th, (col + 1) * tw, (row + 1) * th))
            tile.save(os.path.join(tile_dir, f"geog_bm_{col}_{row}.jpg"), quality=85)
    print(f"wrote basemap + {cols * rows} tiles of {tw}x{th} to {OUT}")


if __name__ == "__main__":
    main()
