

import io
from os.path import exists, join as pjoin, realpath
from shutil import copyfileobj
from typing import Optional, Tuple
from urllib.error import HTTPError
from urllib.request import urlretrieve, urlopen, Request

#external
import numpy
from PIL import Image as Img
import PIL
import mercantile as T


import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def hstack(imgs):
    n = len(imgs)
    assert(n)
    new_im = Img.new('RGB', (256*n, 256))
    for i, im in enumerate(imgs):
        pim = Img.open(im)
        new_im.paste(pim, ((256*i),0))
    return new_im

import numpy as np

def pil_grid(images, max_horiz=np.iinfo(int).max):
    n_images = len(images)
    assert(n_images)
    n_horiz = min(n_images, max_horiz)
    h_sizes, v_sizes = [0] * n_horiz, [0] * (n_images // n_horiz)
    for i, im in enumerate(images):
        if not im: continue
        if isinstance(im, bytes):
            im = Img.open(io.BytesIO(im))
            images[i] = im
        h, v = i % n_horiz, i // n_horiz
        h_sizes[h] = max(h_sizes[h], im.size[0])
        v_sizes[v] = max(v_sizes[v], im.size[1])
    h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
    im_grid = Img.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
    for i, im in enumerate(images):
        if im:
            im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
    return im_grid

def impath_grid(paths):
    return pil_grid([p if isinstance(p, Img.Image) else Img.open(p) if p else None for p in paths])



def myurlretrieve(url, p, referer):
    copyfileobj(urlopen(Request(url, headers={'Referer': referer})), open(p, 'wb'))


def tile_pyramid_url(dest, ll, get_url, zooms=list(range(9, 17))):
    """"build an image from tiles at different zoom levels
        desc: for filenames
        bz,bx,by: base coordinates (for now, should be at highest zoom level bz=maxz)
        tileset: for swisstopo api
        maxz, minz: zoom range to download
    """
    imgs = []
    for z in zooms:
        x, y, z = T.tile(lng=ll.lng, lat=ll.lat, zoom=z)
        # y = (1 << z) - yy - 1 # Flip from TMS to OSM/WebMercator
        # print(x, y, z,  '( from yy=', yy, ')')
        url = get_url(z, x, y)
        referer = None
        if isinstance(url, tuple):
            referer = url[1]
            url = url[0]
        p = pjoin('tiles', url[8:].replace('/', '^'))
        try:
            if not exists(p):
                if referer:
                    myurlretrieve(url, p, referer)
                else:
                    urlretrieve(url, p)
            imgs.append(p)
        except HTTPError as e:
            if e.code != 404:
                # eg 400:  # Bad Request, eg SwissTopo out of decent range
                print('!', e.code, url)
            imgs.append(Img.new('RGB', (256, 256)))
    pilopt = {'quality':99} if dest[-4:] in ('.jpg', 'jpeg') else {}
    impath_grid(imgs).save(dest, **pilopt)
    return dest, *imgs


# previous version, more cumbersome

# def tile_pyramid_url(bdesc, bz, bx, by, maxz, minz, tdesc, get_url):
#     """"build an image from tiles at different zoom levels
#         desc: for filenames
#         bz,bx,by: base coordinates (for now, should be at highest zoom level bz=maxz)
#         tileset: for swisstopo api
#         maxz, minz: zoom range to download
#     """
#     assert maxz >= minz
#     imgs = []
#     for z in range(maxz,minz-1, -1):
#         unz = 2**(bz - z)
#         x, y = bx // unz, by // unz
#         url = get_url(z, x, y)
#         p = pjoin('tiles', url[8:].replace('/', '^'))
#         try:
#             if not exists(p):
#                 urlretrieve(url, p)
#             imgs.append(p)
#         except HTTPError as e:
#             print('!', e.code, url)
#
#     imrg = f'{bdesc}_{tdesc}.png'
#     impath_grid(imgs).save(imrg)
#     return imrg, *imgs


def to_jpeg(im: bytes):
    g = Img.open(io.BytesIO(im))
    output = io.BytesIO()
    g.convert('RGB').save(output, 'JPEG', quality=88)
    return output.getvalue()


def to_numpy(im: Img.Image):
    # https://uploadcare.com/blog/fast-import-of-pillow-images-to-numpy-opencv-arrays/
    im.load()
    # unpack data
    e = Img._getencoder(im.mode, 'raw', im.mode)  # type:ignore
    e.setimage(im.im)

    # NumPy buffer for the result
    shape, typestr = Img._conv_type_shape(im)  # type:ignore
    data = numpy.empty(shape, dtype=numpy.dtype(typestr))
    mem = data.data.cast('B', (data.data.nbytes,))

    bufsize, s, offset = 65536, 0, 0
    while not s:
        l, s, d = e.encode(bufsize)
        mem[offset:offset + len(d)] = d
        offset += len(d)
    if s < 0:
        raise RuntimeError("encoder error %d in tobytes" % s)
    return data


def fill_flood(p_rgb: np.ndarray, f_rgb: np.ndarray, xseed:int, yseed:int, tolerance=12, dilate=4):
    from skimage.segmentation import flood
    from skimage.morphology import dilation, disk

    p_red = p_rgb[..., 1]
    partial_mask = flood(p_red, (xseed, yseed), tolerance=tolerance)
    if dilate:
        partial_mask = dilation(partial_mask, disk(4))
    p_rgb[partial_mask] = f_rgb[partial_mask]
    return p_rgb


NP_WHITE = np.array((255, 255, 255))
NP_BLACK = np.array((0, 0, 0))
NP_RED = np.array((255, 0, 0))
NP_GREEN = np.array((0, 255, 0))


def fill_border(rgbmx, color=NP_RED, *, width=3):
    """fill image in place"""
    N, M, _ = rgbmx.shape
    rgbmx[0:width, :] = color
    rgbmx[N-1-width:, :] = color
    rgbmx[:, 0:width] = color
    rgbmx[:, M-1-width:] = color
    return rgbmx


def rgb_to_bytes(rgbmx, **kw):
    with io.BytesIO() as bout:
        Img.fromarray(rgbmx).save(bout, **kw)
        return bout.getvalue()


def jpeg_wrap(numpy_fun):
    """Wraps function taking & returning ndarray"""
    def w(imd, *a, **kw):
        with io.BytesIO(imd) as bin:
            return rgb_to_bytes(numpy_fun(to_numpy(Img.open(bin)), *a, **kw),
                                format='jpeg', quality=95)
    return w

jpeg_fill_border = jpeg_wrap(fill_border)


def np_equal(mx: np.ndarray, color):
    axis = mx.ndim - 1
    return np.all(mx == color, axis=axis)


def nblackwhite(rgbmx):
    return np.sum(np_equal(rgbmx, NP_BLACK)),\
           np.sum(np_equal(rgbmx, NP_WHITE))

def mask_color(mx, *, color=NP_WHITE, tol=8):
    axis = mx.ndim - 1
    return np.all((mx > color-tol) & (mx < color+tol), axis=axis)

def border_ratio(rgbmx, color):
    N, M, _ = rgbmx.shape
    c = 0
    for x in 0, N-1:
        c += np.sum(np_equal(rgbmx[x, :, :], color))
        # print(x, c)
    for y in 0, M-1:  # corners are counted twice :)
        c += np.sum(np_equal(rgbmx[:, y, :], color))
        # print(y, c)
    return c / ( 2*(N+M) )


def bw_border_ratio(rgbmx):
    return border_ratio(rgbmx, NP_BLACK), border_ratio(rgbmx, NP_WHITE)


def get_color_seed(p_rgb: np.ndarray, tryharder=0, color=NP_WHITE) -> Optional[Tuple[int, int]]:
    """find pixel of given color in array, prioritising corners and borders"""
    c = [(x, y) for x in (0,255) for y in (0,255) if np_equal(p_rgb[x, y], color)]
    if not len(c) and tryharder:
        more = (0,64,128,191,255)
        c = [(x, y) for x in more for y in (0,255) if np_equal(p_rgb[x, y], color)]\
          + [(x, y) for x in (0,255) for y in more if np_equal(p_rgb[x, y], color)]
        if not len(c) and tryharder > 1:
            a = np.where(np_equal(p_rgb, color))
            # if not a: return None, None
            c = (a[0][0], a[1][0]),
    return c[0] if c else None


def has_many_contiguous(mx: np.ndarray, color=NP_WHITE, tol=8):
    """Return true if image has at a strip of "several" pixels of color along border
       - Any image with a strip of >63 will return True
       - Any image with no strip of >32 will return False
       - In between, implementation-defined
    """
    N, M, _ = mx.shape
    T = 32
    for x in range(0, N, T):
        for y in 0, 255:
            if np.sum(mask_color(mx[x:x+T, y], color=color, tol=tol)) == T:
                return x, y
    for y in range(0, M, T):
        for x in 0, 255:
            if np.sum(mask_color(mx[x, y:y+T], color=color, tol=tol)) == T:
                return x, y


def merge_partial_impl(p_rgb: np.ndarray, f_rgb: np.ndarray, **kw) -> Optional[np.ndarray]:
    seed = get_color_seed(p_rgb)
    if seed is None: return None
    return fill_flood(p_rgb, f_rgb, *seed, **kw)

def merge_partial(pdata: bytes, fdata: bytes, **kw):
    pim, fim = Img.open(io.BytesIO(pdata)), Img.open(io.BytesIO(fdata))
    p_rgb = to_numpy(pim)
    f_rgb = to_numpy(fim)
    mat = merge_partial_impl(p_rgb, f_rgb, **kw)
    return None if mat is None else Img.fromarray(mat)

# alternative PIL get_corner
# def merge_partial(pdata: bytes, fdata: bytes, **kw):
#     pim, fim = Img.open(io.BytesIO(pdata)), Img.open(io.BytesIO(fdata))
#     c = [(x, y) for x in (0,255) for y in (0,255) if pim.getpixel((x, y)) == (255, 255, 255)]
#     if not c:
#         return pdata
#     seedy, seedx = c[0]
#     p_rgb = to_numpy(pim)
#     f_rgb = to_numpy(fim)
#     return fillw(pim, fim, seedx, seedy, **kw)
