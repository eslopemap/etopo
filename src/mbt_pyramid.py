import io
import os
import sqlite3

import mercantile as T
import PIL, PIL.Image

import mbt_util as M
from . import img_util as G


def tile_pyramid(dest, ll:T.LngLat, mbt:str, zooms=list(range(9, 17))):
    assert os.path.exists(mbt), mbt
    dbc = sqlite3.connect(mbt).cursor()
    try:
        imgs = []
        for z in zooms:
            imdata = M.lnglat2tile(dbc, z, lng=ll.lng, lat=ll.lat)
            if imdata:
                try:
                    imgs.append(PIL.Image.open(io.BytesIO(imdata)))
                except PIL.UnidentifiedImageError:
                    print('issue: with ', imdata)
                    raise
            else:
                imgs.append(PIL.Image.new('RGB', (256, 256)))
        pilopt = {'quality':99} if dest[-4:] in ('.jpg', 'jpeg') else {}
        G.pil_grid(imgs).save(dest, **pilopt)
        return dest
    finally:
        dbc.connection.close()
