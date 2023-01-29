
# this is insspired by mbt_partial.py
# I tried to make it a bit easier to reuse but didn't finish,
# there was some difficulties around ability to add/remove tiles
# and the read iterator cursor closing itself on concurrent write.

import io
from time import time
import os
from collections import defaultdict
import shutil
import sqlite3

#external
#!pip install shapely
import numpy as np
from PIL import Image as Img
from skimage.metrics import structural_similarity

# own
import mbt_util as M  # type: ignore needs /eslope/development/src in path
from .jpg_quality_pil_magick import get_jpg_quality
from src.mbt_download import catchtime


def imgopen(imd):
    try:
        return Img.open(io.BytesIO(imd))
    except:
        print(len(imd), imd[:20])
        raise

def choose_similar(translate=False):
    def inner(z, x, y, tile_toedit, tile_help1, tile_help2):
        ptedit = imgopen((tile_toedit))
        scores = [-1,-1]
        translations: list[tuple[int, int]] = [(1,1)]  # ie no translation (1px border is ignored)
        if translate:
            # translations = [(dx, dy) for dy in range(3) for dx in range(3)]
            translations = [(1,1), (0,1), (2,1), (1,0), (1,2)]  # sorted and ignoring 0,0 and 2,2
        for dx, dy in translations:
            for r, tile_help in ('1', tile_help1), ('2', tile_help2):
                if tile_help:
                    pth = imgopen((tile_help))
                    ima1in = np.array(ptedit.convert('L'))[1:-1, 1:-1]
                    ima2in = np.array(pth.convert('L'))[dx:256-(2-dx), dy:256-(2-dy)]
                    scoreg = structural_similarity(ima1in, ima2in, full=False)
                    if scoreg > 0.985:
                        return r, tile_help, f't={dx,dy} s={scoreg:.5f} q={get_jpg_quality(pth)}'
                    scores[int(r)-1] = max(scores[int(r)-1], scoreg)
            if max(scores) < 0.3:
                break
        return 'skip', None, f's={scores} q={get_jpg_quality(ptedit)}'
    return inner

def compactdict(d:dict):
    smartstr = lambda e: str(round(e, 2)) if isinstance(e, float) else str(e)
    return ', '.join(':'.join(map(smartstr, kv)) for kv in d.items())

# replace_if_similar

def get_joined_tiles_3(dbc, q='', arraysize=1000): # <- ~30MB RAM
        dbc.execute(
            """SELECT main.tiles.zoom_level, main.tiles.tile_column, main.tiles.tile_row,
                      main.tiles.tile_data, t1.tile_data, t2.tile_data
            FROM main.tiles
            LEFT JOIN help.tiles t1
                ON main.tiles.zoom_level = t1.zoom_level
                AND main.tiles.tile_column = t1.tile_column
                AND main.tiles.tile_row = t1.tile_row
            LEFT JOIN help2.tiles t2
                ON main.tiles.zoom_level = t2.zoom_level
                AND main.tiles.tile_column = t2.tile_column
                AND main.tiles.tile_row = t2.tile_row
            """ + q)
        while rows:= dbc.fetchmany(arraysize):
            for row in rows:
                yield row

def process_tiles(mbt_toedit, mbt_help, mbt_help2, q, get_tiles_cbk, merge_cbk, debugmode=False) -> str:
    """
    Generic merge function
    * for now used to retrieve original version of recompressed jg tile
    * could be adapted for the swisstopo retina merge
    """

    stmt_copy_rows = f'''
        UPDATE out.tiles AS mt SET tile_data = (
            SELECT ht.tile_data FROM help.tiles ht
            WHERE ht.zoom_level = mt.zoom_level AND ht.tile_column=mt.tile_column AND ht.tile_row = mt.tile_row
        ) WHERE zoom_level=? AND tile_column=? AND tile_row=?
    '''

    assert os.path.exists(mbt_toedit), mbt_toedit + ' does not exist'
    assert os.path.exists(mbt_help), mbt_help + ' does not exist'
    mbt_out = mbt_toedit[:-8] + '-processed.mbtiles'
    print(mbt_out)
    if not os.path.exists(mbt_out):
        shutil.copyfile(mbt_toedit, mbt_out)
    db  = sqlite3.connect(mbt_toedit) #, isolation_level="DEFERRED")
    dbc = db.cursor()
    ntiles = M.tile_count(dbc, 'main', q)
    dbout = sqlite3.connect(mbt_out)
    dbcout = dbout.cursor()
    dbc.execute(f'ATTACH ? AS help', (mbt_help,))
    if mbt_help2:
        assert os.path.exists(mbt_help2), mbt_help2 + ' does not exist'
        dbc.execute(f'ATTACH ? AS help2', (mbt_help2,))

    reasons = defaultdict(int)
    elpsd = defaultdict(float)
    copyrows = []
    insrows = []
    rmrows = []
    tilelogname = f'log_{os.path.basename(mbt_toedit)}_{time()}.log'
    f = open(tilelogname, 'w')
    def log(*a):
        print(*a)
        print(*a, file=f)

    def dbsync():
        nonlocal copyrows, insrows, rmrows, elpsd
        if copyrows or rmrows or insrows:
            with catchtime() as tic:
                # dbc.executemany(stmt_copy_rows, copyrows)
                M.remove_tiles(dbc, zxys=rmrows)
            elpsd['db_copyrm'] += tic.time
            with catchtime() as tii:
                M.insert_tiles(dbcout, insrows) #, dbn='out')
            elpsd['db_insert'] += tii.time
            log(f'#{i}/{ntiles}, z{z}: Inserted {len(insrows)} in {tii.time:.1f}s and copied {len(copyrows)} '
                f'and removed {len(rmrows)} in {tic.time:.1f}s')
            copyrows = []
            rmrows = []
            insrows = []
            f.flush()

    try:
        for i, (z, x, y, imd1, imd2, imd3) in enumerate(get_tiles_cbk(dbc, q=q), start=1):
            try:
                if i % 2000 == 1:
                    log(f'#{i}/{ntiles}, z{z}:', compactdict(reasons))
                    log(f'#{i}/{ntiles}, z{z}:', compactdict(elpsd))
                    db.commit()
                if i % 1000 == 1 and (copyrows or rmrows or insrows):
                    dbsync()
                with catchtime() as tim:
                    reason, imd, logs = merge_cbk(z, x, y, imd1, imd2, imd3)
                elpsd['merge_cbk'] += tim.time
                reasons[reason] += 1
                if reason:
                    if reason !='skip':
                        insrows.append((z, x, y, imd))
                    if reason !='skip' or logs:
                        f.writelines(map(str, ('#', i, '/', ntiles, ': ', 'z', z, ' ', x, ' ', y, ' ',
                                            reason, ' ', logs, '\n')))
            except Exception as e:
                if isinstance(e, Img.UnidentifiedImageError):  # type:ignore
                    log('UnidentifiedImageError at ', i, z, x, y)
                    reasons['ImageError'] += 0
                    raise
                else:
                    reasons['Error'] += 0
                    log('Failed at ', i, z, x, y)
                    raise
        dbout.commit()
        log ('Compacting...')
        dbcout.execute('VACUUM')
    finally:
        try:
            dbsync()
            log('finally', compactdict(elpsd))
            log(compactdict(reasons))
        finally:
            try:
                db.commit()
                dbc.close()
                db.close()
                dbout.commit()
                dbcout.close()
                dbout.close()
            finally:
                f.close()
    return mbt_out

