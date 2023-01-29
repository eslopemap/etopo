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


def sh2geojson(sh:BaseGeometry, path, indent=None):
    if not path.endswith('.geojson'):
        path += '.geojson'
    with open(path, 'w') as f:
        f.write(json.dumps(mapping(sh), indent=indent))


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

z10longitudes = [round(tms2southwest(10, x=x, y=1).lng, 5) for x in range(526, 557)]


# ( # the number indicates the lowest TMS zoom to be a tile boundary
# lng49z9_valence , # 4.92
# lng56z6_grenoble_auriol , # 5.62 # eslope walps.W
# lng63z9_digne_thones_pontarlier , # 6.33  # ign 1<>2
# lng70z8_aigle_cannes, # 7.03
# lng77z9_sanremo_zermatt, # 7.73  # eslope walps.E
# lng84z7_zurich_savona, # 8.44
# lng91z9_milano_como , # 9.14
# lng98z8_sondrio_smoritz, # 9.84  # bernina slightly east
# lng105z9_pfunds, # 10.55
# lng112z5_bolzano_innsbruck, # 11.25
# lng119z9_bruneck, # 11.95  # eslope calps.E ; Kompass.z15.E
# lng126z8_lienz, # 12.66
# lng133z9_udine_pocking, # 13.36
# lng140z7_klagenfurt_murau, # 14.06
# lng147z9_277, # 14.77
# lng154z8_graz, # 15.47
# ) = z9longitudes

( # the 2nd number indicates the lowest TMS zoom to be a tile boundary
lng49z9_valence , # 4.92
lng52z10_aix, # 5.27 # ign2/3.W
lng56z6_grenoble_auriol , # 5.62 # eslope walps.W
lng59z10_chambery_toulon, #5.97656 # ign5.W
lng63z9_digne_thones_pontarlier , # 6.33  # ign 1<>2
_lng66z10,
lng70z8_aigle_cannes, # 7.03
lng73z10_monaco_aosta_bern, # 7.38 alps3.E
lng77z9_sanremo_zermatt, # 7.73  # eslope walps.E
lng80z10_imperia_biella,  # 8.08 alps1.E 
lng84z7_zurich_savona, # 8.44
_lng87z10,
lng91z9_milano_como , # 9.14
_lng94z10,
lng98z8_sondrio_smoritz, # 9.84  # bernina slightly east
_lng101z10,
lng105z9_pfunds, # 10.55
_lng108z10,
lng112z5_bolzano_innsbruck, # 11.25
_lng116z10,
lng119z9_bruneck, # 11.95  # eslope calps.E ; Kompass.z15.E
_lng123z10,
lng126z8_lienz, # 12.66
_lng130z10,
lng133z9_udine_pocking, # 13.36
_lng137z10,
lng140z7_klagenfurt_murau, # 14.06
_lng144z10,
lng147z9_277, # 14.77
_lng151z10,
lng154z8_graz, # 15.47
) = z10longitudes

# W->E
# lng52z10_aix = (lng49z9_valence + lng56z6_grenoble_auriol)/2 # 5.27 # ign2/3.W
# lng10zchambery_toulon = (lng56z6_grenoble_auriol + lng63z9_digne_thones_pontarlier)/2  #5.97656 # ign5.W
# lng73z10_monaco_aosta_bern = (lng70z8_aigle_cannes + lng77z9_sanremo_zermatt)/2 # 7.38
lng79z11_ivrea_visp = (3*lng77z9_sanremo_zermatt+ lng84z7_zurich_savona)/4 # 7.9102 frit4.E
# lng80z10_imperia_biella = (lng77z9_sanremo_zermatt + lng84z7_zurich_savona)/2  # 8.08 frit1.E 
lng81z12_albenga = 8.1738  # bugianen_liguria.E
lng124z11_mittersill = (lng119z9_bruneck+ 3*lng126z8_lienz)/4  # 12.48 kompasseast.E

# N->S
(
lat80z8_freiburg,
lat75z9_basel_budapest, # 47.52  # eslope calps.N
lat70z7_morteau_luzern_graz, # 47.04
lat65z9_lausanne_smoritz_bolzano, # 46.56  # eslope walps.N ; ign5
lat60z8_cluses_trento, # 46.07
lat55z9_chambery_biella_trieste, # 45.58  # eslope calps.S ; ign 4<>5
lat50z6_grenoble_torino, # 45.09  # ign 3<>4
lat45z9_gap, # 44.59  # ign 1<>3
lat40z8_digne_tende, # 44.09
lat35z9_antibes, # 43.58  # ign 1&2
lat30z7_toulon, # 43.07
) = z9latitudes

lat77z10_mulhouse = (lat80z8_freiburg + lat75z9_basel_budapest) / 2  # 47.75 k_east.N
lat58z10_mblanc_lecco = (lat60z8_cluses_trento + lat55z9_chambery_biella_trieste) / 2  # 45.83
lat63z10_brigg = (lat60z8_cluses_trento + lat65z9_lausanne_smoritz_bolzano) / 2  # 46.316 k_east.S
lat64z11_= (lat63z10_brigg + lat65z9_lausanne_smoritz_bolzano)/2  # 46.48 kompasseast.S

bbkompass_west = LLBb(lng91z9_milano_como, lat58z10_mblanc_lecco, lng119z9_bruneck, lat75z9_basel_budapest)
# actually NW corner is missing (NW of 10.37/46.68) which brings it close to alps9.SE:
bbkompass_west_snapped = LLBb(lng105z9_pfunds, lat58z10_mblanc_lecco, lng119z9_bruneck, lat75z9_basel_budapest)
# kompass = (lng9_milano_como, lat10_mblanc_lecco, lng8_lienz, )
# actually 12.48 not quite Lienz and 45.82/46.43 not quite como. change at 11.95
bbkompass_east = LLBb(lng119z9_bruneck, lat63z10_brigg, lng124z11_mittersill, lat77z10_mulhouse)
# bbkompass_east_strict = LLBb(lng9_bruneck, 46.37, lng11zmittersill, lat10_mulhouse)

# kompass_strict = (n=lng7_bolzano_innsbruck)

# == BBox used for the slope maps (eslope -> bbox.py) ==
bbwalps = LLBb(5.625, 43.581, 7.734, 46.558)
# bbscalps = BBox(7.734, 45.583, 11.250, 47.517) # "Small" central europe
bbcalps = LLBb(7.734, 45.583, 11.953, 47.517)
bbcalps = LLBb(lng77z9_sanremo_zermatt, lat55z9_chambery_biella_trieste, lng119z9_bruneck, lat75z9_basel_budapest)
bbealps = (11.953, 46.073, 14.062, 47.754)

# bbalps5z10 = LLBb(lng10zchambery_toulon, lat9_chambery_biella_trieste, lng9_sanremo_zermatt, lat9_lausanne_smoritz_bolzano)
# bbalps5 = LLBb(lng6_grenoble_auriol, lat9_chambery_biella_trieste, lng9_sanremo_zermatt, lat9_lausanne_smoritz_bolzano)
bbalps1 = LLBb(lng63z9_digne_thones_pontarlier, lat35z9_antibes, lng80z10_imperia_biella, lat45z9_gap)
bbalps2 = LLBb(lng52z10_aix, lat35z9_antibes, lng63z9_digne_thones_pontarlier, lat45z9_gap)
bbalps3 = LLBb(lng52z10_aix, lat45z9_gap, lng73z10_monaco_aosta_bern, lat50z6_grenoble_torino)
bbalps4z11 = LLBb(lng56z6_grenoble_auriol, lat50z6_grenoble_torino, lng79z11_ivrea_visp, lat55z9_chambery_biella_trieste)
bbalps4 = LLBb(lng56z6_grenoble_auriol, lat50z6_grenoble_torino, lng77z9_sanremo_zermatt+1, lat55z9_chambery_biella_trieste)

bbalps5 = LLBb(lng59z10_chambery_toulon, lat55z9_chambery_biella_trieste, lng70z8_aigle_cannes, lat65z9_lausanne_smoritz_bolzano)
bbalps6 = LLBb(lng70z8_aigle_cannes, lat55z9_chambery_biella_trieste, lng77z9_sanremo_zermatt, lat65z9_lausanne_smoritz_bolzano)

bbalps7 = LLBb(lng77z9_sanremo_zermatt, lat55z9_chambery_biella_trieste, lng91z9_milano_como, lat65z9_lausanne_smoritz_bolzano)
bbalps8 = LLBb(lng91z9_milano_como, lat55z9_chambery_biella_trieste, lng105z9_pfunds, lat65z9_lausanne_smoritz_bolzano)
bbalps9 = LLBb(lng63z9_digne_thones_pontarlier , lat65z9_lausanne_smoritz_bolzano, lng84z7_zurich_savona, lat70z7_morteau_luzern_graz)
bbalps10 = LLBb(lng84z7_zurich_savona, lat65z9_lausanne_smoritz_bolzano, lng105z9_pfunds, lat70z7_morteau_luzern_graz)
bbalps11 = LLBb(8.789, lat70z7_morteau_luzern_graz, lng105z9_pfunds, lat75z9_basel_budapest)

bbalps = {
    1: bbalps1,  # z10 actually z12:Albenga
    2: bbalps2,
    3: bbalps3,
    4: bbalps4z11,  # z11:Biella
    5: bbalps5,
    6: bbalps6,
    7: bbalps7,
    8: bbalps8,
    9: bbalps9,
    10: bbalps10,
    11: bbalps11,
    12: bbkompass_west_snapped,
    13: bbkompass_east
}

bbalp_names = {
    1: 'alps1-Mercantour-Ubaye-Cuneese',
    2: 'alps2-Digne-Aups-Eguilles-Gap',  # IGNt2 - no change
    3: 'alps3-Vercors-Ecrins-Queyras-Cozie',
    # it3: Alpes Cozie (Cotiennes) ; Monviso
    4: 'alps4-Grenoble-Savoie-Susa-Lanzo-GParadiso',
    # Chartreuse, Belledonne, Grandes Rousses N, Arves N, Cerces N, Lauzière, Vanoise, Mont-Cenis
    # it4: Alpes Grées/Alpi Graie: Lanzo, Susa
    #5: 'alps5-Mont-Blanc-Leman-Cervino-Cogne'
    5 : 'alps5-Mont-Blanc-Chambéry-Leman',
    6 : 'alps6-Aoste-Martigny-Gruyère',
    # it6: Gran Paradiso N, Cervino
    7: 'alps7-Ticino-Jungfrau-Lorenzhorn-MtRosa',
    8: 'alps8-Como-Mesolcina-Adamello-Ortler',
    9: 'alps9-CHCW-Vaud-Luzern-Grimselpass',
    10: 'alps10-CHCE-Realp-Pfunds',
    11: 'alps11-CHNE-Zurich-LH-Lechtal',
    12: 'alps12-Arco-Innsbruck-Bruneck-Marmolada',
    13: 'alps13-Civetta--Unterwossen',
}

#LngLatBbox(west=11.95313, south=46.43029, east=11.95312, north=46.67959)


bbwalps = LLBb(lng56z6_grenoble_auriol, lat35z9_antibes, lng77z9_sanremo_zermatt, lat65z9_lausanne_smoritz_bolzano)
bbwalps_i = LLBb(5,43.5,7.72,46.5)
walps = bb2poly(bbwalps)

# Load Swiss & French borders from open data
ch = load_first_feature(pjoin(AREAS_DIR, 'switzerland.geojson'))
fr = load_first_feature(pjoin(AREAS_DIR, 'metropole.geojson'))
assert isinstance(fr, MultiPolygon)
metro = biggest_poly(fr)

# Derived
_frch_holy = cast(Polygon, unary_union([metro, ch]))
frch = Polygon(_frch_holy.exterior.coords)  # type:ignore

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
