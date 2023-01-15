
import os
import sqlite3
import time
from socket import timeout
import sqlite3
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import PIL, PIL.Image
import mercantile as T

import mbt_util as M  # needs /eslope/development/src in path
from bbox import BBox
from . import img_util as G, mbt_download as MD

llswissz9s  = T.LngLat(5.63, 44.37) # SwissTopo z9 used marker

bbchsw = BBox(5.976563, 45.706182,  7.734378, 46.800062)
bbchsc = BBox(7.734378, 45.706182,  9.492183, 46.800062)
bbchse = BBox(9.492183, 46.073229, 10.546877, 46.800062)
bbchc  = BBox(6.328128, 46.800062, 10.546877, 47.040180)
bbchn  = BBox(6.679684, 47.040180,  9.843748, 47.635785)

bbchz10_extent = BBox(3.9, 44.37, 13.36, 48.72)
bbchz10 = bbchz10_extent.snap_to_xyz(z=9, mode='-')  # aubenas-pocking

bbchz12_extent = BBox(5.59, 45.46, 10.88, 47.814) # partial, unlike 45.461
bbchz12 = bbchz12_extent.snap_to_xyz(z=12, mode='-')  # st-geoire-peiting

bbchz9     = BBox(5.63, 44.37, 10.546877, 47.04018)
bbchfr9_1  = BBox(5.63, 44.37, 10.546877, 47.040180)
bbchfr9_2  = BBox(5.63, 45.706182, 5.976563, 45.706182)

bbchfr11_1 = BBox(5.63, 44.37, 10.546877, 45.706182)
bbchfr11_2 = BBox(5.63, 45.706182, 5.976563, 45.706182)

# ==================================================================================================
# Dataset: online resources + arrange them to get a downscaled swisstopo map accross zoom-levels.

def ch_url(tileset, format):  # only landeskarte-10 is png
    return lambda z, x, y: f'https://wmts100.geo.admin.ch/1.0.0/ch.swisstopo.{tileset}/default/current/3857/{z}/{x}/{y}.{format}'



def scale2tileset(scale):
    """For a given scale eg `10` means 1:10, return the the tileset name
       that can be passed to `ch_url` above."""
    if scale==10:
        return 'landeskarte-farbe-10', 'png'
    elif scale == 10000:
        return 'pixelkarte-farbe', 'jpeg'  # 1:10_million not available standalone
    else:
        assert scale in (25, 50, 100, 200, 500, 1000) # 1:25000 to 1:1_million
        return f'pixelkarte-farbe-pk{scale}.noscale', 'jpeg'


def geturl_ch_downsampled(z, x, y):
    """Downsampling is handled by requesting the layer at a lower zoom-level.
       For example the layer pixelkarte-farbe-pk-25,
       shown on swisstopo.ch at zoom-level z16, is requested at z15 instead.
       This basically undoes the retina effect, gaining back storage space :)"""
    return ch_url(*scale2tileset(dw_tilescale[z]))(z, x, y)


#           [...9,         10,   11,  12,  13,  14, 15, 16, 17]
tilescale = [10000] * 10 + [1000, 1000, 500, 200, 100, 50, 25, 10]
dw_tilescale = [10000]*9 + [1000, 1000, 500, 200, 100, 50, 25, 10]



# ==================================================================================================
# partial/empty tile handling

def ch_fill(mbt_to_fill, mbt_fulltiles):
    """Try to fill any empty or partial tile in `mbt_to_fill` from upscale
       Currently there are 2 hardcoded sources:
       (1) `mbt_full_tiles`
       (2) online swisstopo base map `pixelkarte-farbe`"""
    get_url = ch_url('pixelkarte-farbe', 'jpeg')
    dest = 'zz' + mbt_to_fill
    assert os.path.exists(mbt_to_fill)
    dbr = sqlite3.connect(mbt_to_fill)
    assert os.path.exists(mbt_fulltiles)
    dbrfull = sqlite3.connect(mbt_fulltiles)
    isnew =  not os.path.exists(dest)
    dbw = sqlite3.connect(dest).cursor()
    if isnew:
        M.create_mbt(dbw, 'main')
        dbw.execute(f'ATTACH ? AS orig', (mbt_to_fill,))
        dbw.execute('INSERT INTO main.metadata SELECT * FROM orig.metadata')
    rows = []
    ntot, dwntime, cnvtime  = 0, 0, 0
    try:
        for zf in (range(10, 17)):  # zoom to fill
            # iterate over parent (z - 1) tiles, because if they exist, (some of) their zoom will exist
            for i, parent_tile in enumerate(M.get_all_coords(dbr, q=f'WHERE zoom_level = {zf-1}')):
                if i % 100 == 1:
                    if i % 1000 == 1 and not rows:
                        print(f'At: {i} for z{zf}')
                    if rows:
                        with MD.catchtime() as ti:
                            M.insert_tiles(dbw, rows)
                        ntot += len(rows)
                        print(f'Added {len(rows)} tiles in {dwntime:.1f} + {cnvtime:.3f} + {ti.time:.3f} seconds.'
                            f' At: {i-1} for z{zf}. {ntot} downloaded so far.')
                        rows = []
                        dwntime = cnvtime = 0
                for xoff in (0, 1):
                    for yoff in (0,1):
                        pz, px, py = parent_tile
                        child_tile_tms = zf, px*2 + xoff, py*2 + yoff
                        child_tile_zxy = zf, px*2 + xoff, (1<<zf) - (py*2 + yoff) - 1
                        # if child tile not in the *not partial* parent and not already downloaded:
                        if not M.num2tile(dbrfull, *child_tile_tms, flip_y=False)\
                                and not M.num2tile(dbw, *child_tile_tms, flip_y=False):
                            # print(pz, py, px, '->', *child_tile_tms)
                            dt, ct = MD.download_tile_retry(format, get_url, rows, *child_tile_zxy)
                            dwntime += dt
                            cnvtime += ct
    finally:
        with MD.catchtime() as ti:
            M.insert_tiles(dbw, rows)
        print(f'Added {len(rows)} tiles in {dwntime:.1f} + {cnvtime:.4f} + {ti.time:.4f} seconds.'
                f' {ntot} downloaded so far. done!')
        dbw.connection.commit()
        dbw.close()
        dbw.connection.close()
