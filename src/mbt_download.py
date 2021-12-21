import os
import sqlite3
import time
from socket import timeout
from typing import List
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import mercantile as T

import mbt_util as M  # needs /eslope/development/src in path
from . import img_util as G


class catchtime:
    def __enter__(self):
        self.time = time.perf_counter()
        return self
    def __exit__(self, type, value, traceback):
        self.time = time.perf_counter() - self.time


def bbox_to_mbt(dest: str, bbox, zooms: List[int], format:str, get_url, reuse:bool=True):
    # shrink bounds to avoid extraneous tiles due to float precision of TMS tile boundaries.
    bb = bbox.enlarge(-0.000005).astuple()
    tiles = list(T.tiles(*bb, zooms))  # type:ignore
    return tiles_to_mbt(dest, tiles, bbox, format, get_url, reuse)


def tiles_to_mbt(dest: str, tiles:List[T.Tile], bbox, format:str, get_url, reuse:bool=True):
    """"build an mbtiles file from tiles at different zoom levels,
        downloaded on the fly. No attempt is made at parallelizing download to stay within fair use.
        `tiles` and `get_url` use XYZ (https://gist.github.com/tmcw/4954720)
        Example call:
        ```MD.tiles_to_mbt('foo.mbtiles', [T.Tile(34616,23175, 16)], bbox=None,
                           format='jpeg', get_url=SS.ch_url('pixelkarte-farbe', 'jpeg'))```
        :param dest: mbtiles path
        :param bbox: bounds, for mbtiles metadata only
        :param zooms: list of TMS zoom levels (1 to 20, usually 7<>17)
        :param format: as per mbtiles metadata png or jpeg. not all software accepts mixing them
        :param geturl: function given `z, x, y` in WebMercator, must return URL to be used to get the tile
        :param reuse: whether to skip downloading existing tiles
    """
    isnew = not os.path.exists(dest)
    dbc = sqlite3.connect(dest).cursor()
    if isnew:
        M.create_mbt(dbc)
        M.create_mbt_meta(dbc, dest[:-8], '', bbox.astuple(), format)
    ntiles = len(tiles)
    i, dwntime, cnvtime  = 0, 0, 0
    # `rows` to insert in db are batched for (premature) optimisation.
    rows = []
    try:
        for i, (x, y, z) in enumerate(tiles, start=1):
            if i % 100 == 1:
                with catchtime() as ti:
                    M.insert_tiles(dbc, rows)
                print(f'Added {len(rows)} tiles in {dwntime:.1f} + {cnvtime:.3f} + {ti.time:.3f} seconds.'
                      f' Status: {i-1} / {ntiles}')
                rows = []
                dwntime = cnvtime = 0
            if reuse and M.num2tile(dbc, z, x, y, flip_y=True):
                continue
            dt, ct = download_tile_retry(format, get_url, rows, z, x, y)
            dwntime += dt
            cnvtime += ct

    finally:
        with catchtime() as ti:
            M.insert_tiles(dbc, rows)
        print(f'Added {len(rows)} tiles in {dwntime:.1f} + {cnvtime:.4f} + {ti.time:.4f} seconds.'
                f' Status: done!')
        dbc.connection.commit()
        dbc.close()
        dbc.connection.close()


def download_tile_retry(format, get_url, rows, z, x, y):
    url = get_url(z, x, y)
    ntries, dwntime, cnvtime = 0, 0, 0
    while ntries < 4:
        ntries += 1
        try:
            with catchtime() as t:
                im = urlopen(url, timeout=2).read()  # using headers from line 30
            dwntime += t.time
            with catchtime() as t:
                if format == 'jpeg' and url.endswith('.png'):
                    im = G.to_jpeg(im)
            cnvtime += t.time
            rows.append((z, x, (1 << z) - y - 1, im))
            break
        except HTTPError as e:
            print('!', e.code, url)
            if e.code == 404:  # not found, skip
                break
            elif e.code == 400: # bad request
                break
        except (URLError, ConnectionError, timeout) as e:
            print('!', e, url)
            time.sleep(20)
    return dwntime, cnvtime
