from collections import defaultdict
import io
import os
import shutil
import sqlite3
import time

import PIL, PIL.Image

import mbt_util as M  # needs /eslope/development/src in path
from . import img_util as G
from .mbt_download import catchtime


def clean_missing_data(mbt: str, *, w, T, zlevels:tuple=(), debug=True):
    """Clean file in place.

    It uses the following heuristics, valid only for jpeg tiles as png will have less colors
    * Tile size < 4000 bytes (encoded) or with less than 300 different colors is empty
    * Otherwise count pure black + pure white pixels, X
    * X < 10% of pixels: empty
    * 10% < X < 80%: partial
    Based on this:
    * Empty tiles are discarded
    * Partial tiles are moved to a dedicated mbtiles for later use (ie possibly merge with other tilesets :-))
    Typical values for IGN w=0.1, T=192|255 ; for swisstopo w=0.04, T=96
    """
    debug = print if debug else lambda x: None
    assert mbt.endswith('.mbtiles')
    newmbt = mbt[:-8] + '-clean.mbtiles'
    if os.path.exists(newmbt):
        os.rename(newmbt, mbt[:-8] + str(round(time.time())) + '-clean.mbtiles')
    shutil.copyfile(mbt, newmbt)
    mbt = newmbt
    zxy_to_remove = []
    reasons = defaultdict(int)
    db = sqlite3.connect(mbt, isolation_level="DEFERRED")
    delcur = db.cursor()
    # Prepare partial tiles db
    partialmbt = mbt.replace('clean', 'partial')
    if os.path.exists(partialmbt):
        os.rename(partialmbt, mbt[:-8] + str(round(time.time())) + '-partial.mbtiles')
    delcur.execute(f'ATTACH ? AS partial', (partialmbt,))
    M.create_mbt(delcur, 'partial')
    delcur.execute('INSERT INTO partial.metadata SELECT * FROM main.metadata')
    ntiles = M.tile_count(delcur)
    q = '' if not zlevels else f'WHERE zoom_level IN {zlevels}'

    for i, (z, x, y, imd) in enumerate(M.get_all_tiles(db, q=q), start=1):
        if i % 2000 == 1:
            M.remove_tiles(delcur, zxy_to_remove)
            print(f'Deleted {len(zxy_to_remove)}. Status: {i-1} / {ntiles}')
            zxy_to_remove = []
        try:
            reason, _, _ = classify_tile(imd, w_threshold=w, T=T)
        except Exception as e:
            import traceback as tb
            tb.print_exc()
            print(f"tile {z,x,y} : error during detection, keeping it")
            reason = e.__class__

        # PIXELS = 256**2
        # im = PIL.Image.open(io.BytesIO(imd))
        # reason = ''
        # if len(imd) < 4000:
        #     reason += 'small'
        #     zxy_to_remove.append((z, x, y))
        # else:
        #     colors = im.getcolors(256**2)
        #     if len(colors) < 300:
        #         reason += 'fewcolors'
        #         zxy_to_remove.append((z, x, y))
        #     else:
        #         nbw = 0
        #         for n, c in colors:
        #             if c in ((255,255,255),(0,0,0)):
        #                 nbw += n
        #         if nbw > 0.8 * PIXELS:
        #             reason += 'tooblackorwhite'
        #             zxy_to_remove.append((z, x, y))
        #         elif nbw > 0.1 * PIXELS:
        #             reason += 'partial'

        if reason in ('black', 'white', 'cross', 'black&white'):
            zxy_to_remove.append((z, x, y))
        if reason == 'partial':
            delcur.execute('INSERT INTO partial.tiles SELECT * FROM main.tiles '
                        'WHERE zoom_level=? AND tile_column=? AND tile_row=?', (z, x, y))
            zxy_to_remove.append((z, x, y))
        # reason = f'{z} {reason}'
        reasons[reason] += 1
        # if reason:
        #     debug(f"tile {z,x,y} : {reason} {newr or '!!!!'}")
    M.remove_tiles(delcur, zxy_to_remove)
    print(f'Deleted {len(zxy_to_remove)}. Status: done!')
    db.commit()
    return mbt, reasons


def compactdict(d:dict):
    smartstr = lambda e: str(round(e, 2)) if isinstance(e, float) else str(e)
    return ', '.join(':'.join(map(smartstr, kv)) for kv in d.items())

# These are quite specific to Swisstopo maps
EMPTY_LENGTHS = {1651: 'white', 1652: 'black', 2976: 'chcross', 810: 'chcross'}

def classify_tile(imd, w_threshold = 0.04, T=64):
    # todo use this to discard downloaded images whichare mostly partial (eg with crosses)
    N = len(imd)
    rgbmx, seed = None, None
    if N in EMPTY_LENGTHS:
        reason = 'white' if N==1651 else 'black' if N==1652 else 'cross'
    else:
        rgbmx = G.to_numpy(PIL.Image.open(io.BytesIO(imd)))
        _, _, dim = rgbmx.shape
        if dim != 3:
            # image has {dim} channels (4:transparency) but the code only supports 3 for now
            reason = f'skipped_dim_{dim}'
        else:
            nblack, nwhite = G.bw_border_ratio(rgbmx)
            # print(nblack, nwhite)
            if nwhite + nblack > 0.97:
                reason = 'black&white'
            elif nwhite > w_threshold and (
                    seed := G.has_many_contiguous(rgbmx, color=G.NP_WHITE, tolerance_color=8, T=T)):
                reason = 'partial'
            else:
                reason = '' # normal tile
    return reason, rgbmx, seed


def fill_partial_data(mbt_tofill, mbt_help, fallback_cbk=None, debugmode=False):
    stmt_copy_rows = f'''
        UPDATE main.tiles AS mt SET tile_data = (
            SELECT ht.tile_data FROM help.tiles ht
            WHERE ht.zoom_level = mt.zoom_level AND ht.tile_column=mt.tile_column AND ht.tile_row = mt.tile_row
        ) WHERE zoom_level=? AND tile_column=? AND tile_row=?
    '''

    assert os.path.exists(mbt_tofill)
    assert os.path.exists(mbt_help)
    db  = sqlite3.connect(mbt_tofill, isolation_level="DEFERRED")
    dbc = db.cursor()
    ntiles = M.tile_count(dbc)
    dbc.execute(f'ATTACH ? AS help', (mbt_help,))
    helpts = M.Tileset.from_db(dbc, dbname='help')
    reasons = defaultdict(int)
    elpsd = defaultdict(float)
    copyrows = []
    insrows = []
    rmrows = []
    tilelogname = f'log_{os.path.basename(mbt_tofill)}_{time.time()}.log'
    f = open(tilelogname, 'w')

    def dbsync():
        nonlocal copyrows, insrows, rmrows, elpsd
        if copyrows:
            with catchtime() as tic:
                dbc.executemany(stmt_copy_rows, copyrows)
                M.remove_tiles(dbc, zxys=rmrows)
            elpsd['db_copyrm'] += tic.time
            with catchtime() as tii:
                M.insert_tiles(dbc, insrows)
            elpsd['db_insert'] += tii.time
            print(f'#{i}/{ntiles}, z{z}: Inserted {len(copyrows)} in {tii.time:.1f}s and copied {len(copyrows)} '
                  f'and removed {len(rmrows)} in {tic.time:.1f}s')
            copyrows = []
            insrows = []
            rmrows = []
            f.flush()

    try:
        for i, (z, x, y, imd) in enumerate(M.get_all_tiles(db), start=1):
            nwhite = nblack = -1  # log
            # has_help = lambda: M.num2tile(dbc, z, x, y, flip_y=False, what='1', dbname='help')
            if i % 2000 == 1:
                print(f'#{i}/{ntiles}, z{z}:', compactdict(reasons))
                print(f'#{i}/{ntiles}, z{z}:', compactdict(elpsd))
                db.commit()
            if i % 200 == 1 and copyrows:
                dbsync()
            N = len(imd)
            if N in EMPTY_LENGTHS:
                reason = 'white' if N==1651 else 'black' if N==1652 else 'cross'
                if (z, x, y) in helpts:
                    copyrows.append((z, x, y))
                    reason += ':overwrite'
                # elif fallback_cbk:
                #     imhelp = fallback_cbk(z, x, y)
                #     reason += ':downloaded'
                else:
                    rmrows.append((z, x, y))
                    reason += ':nohelp:remove'
            else:
                rgbmx = G.to_numpy(PIL.Image.open(io.BytesIO(imd)))
                nblack, nwhite = G.bw_border_ratio(rgbmx)
                if nwhite + nblack > 0.97:
                    if (z, x, y) in helpts:
                        copyrows.append((z, x, y))
                        reason = 'black&white:overwrite'
                    else:
                        rmrows.append((z, x, y))
                        reason = 'black&white:nohelp:remove'
                elif nwhite > 0.02 and (seed := G.has_many_contiguous(rgbmx, color=G.NP_WHITE, tolerance_color=8)):
                    reason = 'partial'
                    imhelp = M.num2tile(dbc, z, x, y, flip_y=False, dbname='help')
                    if not imhelp and fallback_cbk:
                        with catchtime() as ti:
                            imhelp = fallback_cbk(z, x, y)
                        elpsd['download'] += ti.time
                        r, _, _ = classify_tile(imhelp)
                        reason += ':downloaded:' + r
                        if r:
                            imhelp = None
                        else:
                            if debugmode: imhelp = G.jpeg_fill_border(imhelp, G.NP_GREEN, width=3)
                            with catchtime() as ti:
                                M.insert_tiles(dbc, [(z, x, y, imhelp)], dbname='help')
                            elpsd['insertdwn'] += ti.time
                    else:
                        r, _, _ = classify_tile(imhelp)
                    if r or not imhelp:
                        reason += (':help-' + r) if r else ':notfound'
                        if nwhite > 0.2:  # too much white & no solution -> remove
                            reason += ':remove'
                            rmrows.append((z, x, y))
                        else:
                            reason += ':keep'
                    else:
                        with catchtime() as ti:
                            dilate = 4 if z == 16 else 1
                            rgbmx_help = G.to_numpy(PIL.Image.open(io.BytesIO(imhelp)))
                            rgbmx_merged = G.fill_flood(rgbmx, rgbmx_help, *seed, dilate=dilate)
                            if debugmode: G.fill_border(rgbmx_merged, G.NP_RED)
                            jpg_merged = G.rgb_to_bytes(rgbmx_merged, format='jpeg', quality=95)
                        elpsd['merge'] += ti.time
                        insrows.append((z, x, y, jpg_merged))
                        reason += ':merged'
                else:
                    reason='skip'
            reasons[reason] += 1
            # if reason != 'skip': print(z, x, y, reason)
            if reason != 'skip':
                f.writelines(map(str, ('#', i, '/', ntiles, ': ', 'z', z, ' ', x, ' ', y, ' ',
                                       reason, nwhite, nblack, '\n')))
        return tilelogname
    finally:
        try:
            dbsync()
            print(compactdict(elpsd))
            print(compactdict(reasons))
        finally:
            try:
                db.commit()
                dbc.close()
                db.close()
            finally:
                f.close()

