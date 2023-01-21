import logging
import sys
import json
from os.path import exists, join as pjoin, realpath
from pathlib import Path
from typing import cast

#external
#!pip install shapely
import shapely
from shapely.geometry import mapping, shape, GeometryCollection, Polygon, Point, MultiPolygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
import mercantile as T

AREAS_DIR = realpath(pjoin(__file__, '../../data/areas'))

LLBb = T.LngLatBbox

def load_first_feature(path: str, buffer=True) -> BaseGeometry:
    assert path.endswith('json')
    # We could use GeometryCollection if there's > 1
    with open(path) as f:
        root = json.load(f)
        if "features" in root:
            assert len(root["features"]) == 1
            root = root["features"][0]
        # NOTE: buffer(0) is a trick for fixing scenarios where polygons have overlapping coordinates
        return shape(root["geometry"]).buffer(0)


def biggest_poly(multipoly: MultiPolygon):
    return multipoly.geoms[max((g.area, i) for i, g in enumerate(multipoly.geoms))[1]]


def bb2poly(bb: T.LngLatBbox):
    return Polygon([
        Point(bb.west, bb.north),
        Point(bb.west, bb.south),
        Point(bb.east, bb.south),
        Point(bb.east, bb.north),
        Point(bb.west, bb.north)
    ])


def sh2geojson(sh:BaseGeometry, path):
    if not path.endswith('.geojson'):
        path += '.geojson'
    with open(path, 'w') as f:
        f.write(json.dumps(mapping(sh)))


# def bounds2poly(bounds_tuple):
#     west, north, east, south = bounds_tuple
#     return Polygon([
#         Point(west, north),
#         Point(west, south),
#         Point(east, south),
#         Point(east, north),
#         Point(west, north)
#     ])

# camargue-macon-sanremo-zermatt

# bbchsw = BBox(5.976563, 45.706182,  7.734378, 46.800062)
# bbchsc = BBox(7.734378, 45.706182,  9.492183, 46.800062)
# bbchse = BBox(9.492183, 46.073229, 10.546877, 46.800062)
# bbchc  = BBox(6.328128, 46.800062, 10.546877, 47.040180)
# bbchn  = BBox(6.679684, 47.040180,  9.843748, 47.635785)

#there is an south-east corner at adamello at z10 and z12: 10.54/46.07
#z11 goes much further (south milano east garda 10.80/45.46)

def tms2southwest(z, x, y) -> T.LngLat:
    """Return south_west corner of given TMS tile"""
    # Mercantile uses TXYZ but MBTiles use TMS -> flip
    y = (1 << z) - y - 1
    bb = T.xy_bounds(x, y, z)
    return T.lnglat(bb.left, bb.bottom)

# lng9_valence = 

z9longitudes = [round(tms2southwest(9, x=x, y=1).lng, 5) for x in range(263, 279)]
z9latitudes = [round(tms2southwest(9, x=1, y=y).lat, 5) for y in reversed(range(324, 335))]


( # the number indicates the lowest TMS zoom to be a tile boundary
lng9_valence , # 4.92
lng6_grenoble_auriol , # 5.62 # eslope walps.W
lng9_digne_thones_pontarlier , # 6.33  # ign 1<>2
lng8_aigle_cannes, # 7.03
lng9_sanremo_zermatt, # 7.73  # eslope walps.E
lng7_zurich_savona, # 8.44
lng9_milano_como , # 9.14
lng8_sondrio_smoritz, # 9.84  # bernina slightly east
lng9_pfunds, # 10.55
lng5_bolzano_innsbruck, # 11.25
lng9_bruneck, # 11.95  # eslope calps.E ; Kompass.z15.E
lng8_lienz, # 12.66
lng9_udine_pocking, # 13.36
lng7_klagenfurt_murau, # 14.06
lng9_277, # 14.77
lng8_graz, # 15.47
) = z9longitudes


# W->E
lng10_aix = (lng9_valence + lng6_grenoble_auriol)/2 # 5.27 # ign2/3.W
lng10_chambery_toulon = (lng6_grenoble_auriol + lng9_digne_thones_pontarlier)/2  #5.97656 # ign5.W
lng11_ivrea_visp = (3*lng9_sanremo_zermatt+ lng7_zurich_savona)/4 # 7.9102 frit4.E
lng10_imperia_biella = (lng9_sanremo_zermatt + lng7_zurich_savona)/2  # 8.08 frit1.E 
lng12_albenga = 8.1738  # bugianen_liguria.E
lng11_mittersill = (lng9_bruneck+ 3*lng8_lienz)/4  # 12.48 kompasseast.E

# N->S
(
lat8_freiburg,
lat9_basel_budapest, # 47.52  # eslope calps.N
lat7_morteau_luzern_graz, # 47.04
lat9_lausanne_smoritz_bolzano, # 46.56  # eslope walps.N ; ign5
lat8_cluses_trento, # 46.07
lat9_chambery_biella_trieste, # 45.58  # eslope calps.S ; ign 4<>5
lat6_grenoble_torino, # 45.09  # ign 3<>4
lat9_gap, # 44.59  # ign 1<>3
lat8_digne_tende, # 44.09
lat9_antibes, # 43.58  # ign 1&2
lat7_toulon, # 43.07
) = z9latitudes

lat10_mulhouse = (lat8_freiburg + lat9_basel_budapest) / 2  # 47.75
lat10_mblanc_lecco = (lat8_cluses_trento + lat9_chambery_biella_trieste) / 2  # 45.83
lat10_brigg = (lat8_cluses_trento + lat9_lausanne_smoritz_bolzano) / 2  # 46.316 k_east.S
lat11_= (lat10_brigg + lat9_lausanne_smoritz_bolzano)/2  # 12.48 kompasseast.S

bbkompass_west = LLBb(lng9_milano_como, lat10_mblanc_lecco, lng9_bruneck, lat9_basel_budapest)
# actually NW corner is missing (NW of 10.37/46.68) which brings it close to alps9.SE:
bbkompass_west_snapped = LLBb(lng9_pfunds, lat10_mblanc_lecco, lng9_bruneck, lat9_basel_budapest)
# kompass = (lng9_milano_como, lat10_mblanc_lecco, lng8_lienz, )
# actually 12.48 not quite Lienz and 45.82/46.43 not quite como. change at 11.95
bbkompass_east = LLBb(lng9_bruneck, lat10_brigg, lng11_mittersill, lat10_mulhouse)
# bbkompass_east_strict = LLBb(lng9_bruneck, 46.37, lng11_mittersill, lat10_mulhouse)

# kompass_strict = (n=lng7_bolzano_innsbruck)

# == BBox used for the slope maps (eslope -> bbox.py) ==
bbwalps = LLBb(5.625, 43.581, 7.734, 46.558)
# bbscalps = BBox(7.734, 45.583, 11.250, 47.517) # "Small" central europe
bbcalps = LLBb(7.734, 45.583, 11.953, 47.517)
bbcalps = LLBb(lng9_sanremo_zermatt, lat9_chambery_biella_trieste, lng9_bruneck, lat9_basel_budapest)
bbealps = (11.953, 46.073, 14.062, 47.754)

# should be 1
bbalps5z10 = LLBb(lng10_chambery_toulon, lat9_chambery_biella_trieste, lng9_sanremo_zermatt, lat9_lausanne_smoritz_bolzano)
bbalps5 = LLBb(lng6_grenoble_auriol, lat9_chambery_biella_trieste, lng9_sanremo_zermatt, lat9_lausanne_smoritz_bolzano)
bbalps4z10 = LLBb(lng6_grenoble_auriol, lat6_grenoble_torino, lng11_ivrea_visp, lat9_chambery_biella_trieste)
bbalps4 = LLBb(lng6_grenoble_auriol, lat6_grenoble_torino, lng9_sanremo_zermatt+1, lat9_chambery_biella_trieste)
bbalps3z10 = LLBb(lng10_aix, lat9_gap, lng9_sanremo_zermatt, lat6_grenoble_torino)
bbalps3 = LLBb(lng9_valence, lat9_gap, lng9_sanremo_zermatt, lat6_grenoble_torino)
bbalps2z10 = LLBb(lng10_aix, lat9_antibes, lng9_digne_thones_pontarlier, lat9_gap)
bbalps2 = LLBb(lng9_valence, lat9_antibes, lng9_digne_thones_pontarlier, lat9_gap)
bbalps1z10 = LLBb(lng9_digne_thones_pontarlier, lat9_antibes, lng10_imperia_biella, lat9_gap)
# bbalps1z10 = LLBb(lng9_digne_thones_pontarlier, lat9_antibes, lng12_albenga, lat9_gap)
bbalps1 = LLBb(lng9_digne_thones_pontarlier, lat9_antibes, lng7_zurich_savona, lat9_gap)

bbalps6 = LLBb(lng9_sanremo_zermatt, lat9_chambery_biella_trieste, lng9_milano_como, lat9_lausanne_smoritz_bolzano)
bbalps7 = LLBb(lng9_milano_como, lat9_chambery_biella_trieste, lng9_pfunds, lat9_lausanne_smoritz_bolzano)
bbalps8 = LLBb(lng9_digne_thones_pontarlier , lat9_lausanne_smoritz_bolzano, lng7_zurich_savona, lat7_morteau_luzern_graz)
bbalps9 = LLBb(lng7_zurich_savona, lat9_lausanne_smoritz_bolzano, lng9_pfunds, lat7_morteau_luzern_graz)

bbalps = {
    1: bbalps1z10,
    2: bbalps2z10,
    3: bbalps3z10,
    4: bbalps4z10,
    5: bbalps5z10,
    6: bbalps6,
    7: bbalps7,
    8: bbalps8,
    9: bbalps9,
    10: bbkompass_west_snapped,
    12: bbkompass_east

#LngLatBbox(west=11.95313, south=46.43029, east=11.95312, north=46.67959)

}

bbwalps = LLBb(lng6_grenoble_auriol, lat9_antibes, lng9_sanremo_zermatt, lat9_lausanne_smoritz_bolzano)
bbwalps_i = LLBb(5,43.5,7.72,46.5)
walps = bb2poly(bbwalps)

# Load Swiss & French borders from open data
ch = load_first_feature(pjoin(AREAS_DIR, 'switzerland.geojson'))
fr = load_first_feature(pjoin(AREAS_DIR, 'metropole.geojson'))
assert isinstance(fr, MultiPolygon)
metro = biggest_poly(fr)

# Derived
_frch_holy = cast(Polygon, unary_union([metro, ch]))
frch = Polygon(_frch_holy.exterior.coords)

# These have been derived from the open data above with the functions below
itwalps = shape(json.load(open(pjoin(AREAS_DIR, 'it-alps-sanremo.geojson'))))
# this one is special to avoid losing Bugiane in te Ivrea-Biella area (Gran paradiso)
itwalps_ivrea = shape(json.load(open(pjoin(AREAS_DIR, 'it-alps-ivrea.geojson'))))



def cut_walps_sanremo():
    global itwalps
    # walpsfrch = walps.intersection(frch)
    walpsit = walps.difference(frch)
    with open(pjoin(AREAS_DIR, 'it-alps-sanremo.geojson'), 'w') as f:
        f.write(json.dumps(mapping(walpsit)))
    return itwalps

def cut_walps_ivrea():
    global itwalps_ivrea
    walps_ivrea = bb2poly(bbwalps._replace(east=7.91016))
    # walpsfrch = walps_ivrea.intersection(frch)
    walpsit = walps_ivrea.difference(frch)
    with open(pjoin(AREAS_DIR, 'it-alps-ivrea.geojson'), 'w') as f:
         f.write(json.dumps(mapping(walpsit)))
    itwalps_ivrea = shape(json.load(open(pjoin(AREAS_DIR, 'it-alps-ivrea.geojson'))))
    return itwalps_ivrea

def cut_walps_ligure():
    global itwalps_ligure
    walps_ligure = bb2poly(bbwalps._replace(east=8.173828))
    # walpsfrch = walps_ligure.intersection(frch)
    walpsit = walps_ligure.difference(frch)
    with open(pjoin(AREAS_DIR, 'it-alps-ligure.geojson'), 'w') as f:
         f.write(json.dumps(mapping(walpsit)))
    itwalps_ligure = shape(json.load(open(pjoin(AREAS_DIR, 'it-alps-ivrea.geojson'))))
    return itwalps_ligure

def alps2geojson(path):
    sh2geojson(MultiPolygon(map(bb2poly, bbalps.values())), path)
