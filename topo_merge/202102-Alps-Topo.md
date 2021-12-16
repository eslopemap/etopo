# Unified Alps border

I wanted to make a single map that works on both sides of the border, for hiking and ski-touring.
Unfortunately the last good paper maps (IGN's ASF Alpes Sans Frontières) were discontinued years ago, and have no online equivalent anyway.

I took the excellent Bugianen map on the Italian side (open), and IGN on the french side (access plan on [ignrando](https://ignrando.fr/boutique/iphigenie-gpp-an.html)).

Understanding mbtiles
---------------------

I found this helper very useful to quickly inspect an mbtile

```
tile() { # tile $mbtiles $x $y $z
  mkdir -p ${1/.mbtiles/}-tiles
  ext=$(sqlite3 "$1" "SELECT value FROM metadata WHERE name='format'")
  q="SELECT writefile('${1/.mbtiles/}-tiles/$4-$2-$3.$ext', tile_data) FROM tiles WHERE tile_column=$2 AND tile_row=$3 AND zoom_level=$4 LIMIT 1"
  echo sqlite3 \""$1"\" \""$q"\"  # "
  sqlite3 "$1" "$q"
}
```

Example use:

```
tile Bugianen\ 2005\ Cuneese.mbtiles 34159 41752 16`
identify -verbose 'Bugianen 2005 Cuneese-tiles/16-34159-41752.jpg'
```

... which allow us to find that Bugianen uses jpgs with Quality: 80 (whereas from IGN APIs we get Quality: 75)

Step 1: Make the cutline
#########

We are going to cut on the border, slightly inland on on side so that the border is "clean -- arbtirarily, on the french side, by 0.001 degrees (works well for levels 12-14, but should be 0.0005 for levels 15-16)

First let's get the borders:

```bash
wget https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/metropole.geojson
wget https://raw.githubusercontent.com/ZHB/switzerland-geojson/master/country/switzerland.geojson
wget https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson

```

For now we'll only use the french border, and we first need to remove islands.
`ogr` wasn't very ergonomic so I use `shapely`. Comments inline:

(!) TODO simplify this: we just need to load (A) camargue-macon-sanremo-tile  (B) italy (eg piemont+aoste), and A - B.buffer(0.001). This will solve the eaten sea-border issue.

I can even interesect (B) with the bbox of Bugianen maps, to allow the french map to go around it on the italian side.

```python
from shapely.geometry import mapping, shape, GeometryCollection, Polygon
from shapely.ops import cascaded_union

def load_first_feature(path):
    # We could use GeometryCollection if there's > 1
    with open(path) as f:
        root = json.load(f)
        if "features" in root:
            assert len(root["features"]) == 1
            root = root["features"][0]
        # NOTE: buffer(0) is a trick for fixing scenarios where polygons have overlapping coordinates
        return shape(root["geometry"]).buffer(0)

def biggest_poly(multipoly):
    return multipoly.geoms[max((g.area, i) for i, g in enumerate(fr.geoms))[1]]

# Load French borders
fr = load_first_feature('metropole.geojson')
# France is the biggest french territory
metro = biggest_poly(fr)

# We want switzerland to count like it's french (ie, we want the italian Bugianen map to at into it as well) so:
frch_holy = cascaded_union([metro, ch])
frch = Polygon(frch_holy.exterior.coords)
with open('frch.geojson', 'w') as f: f.write(json.dumps(mapping(frch)))

# We work only on the western alps (plus a tiny buffer):
walps = load_first_feature('camargue-macon-sanremo-tile.geojson').buffer(0.007)
# alpsw_frch = tile.intersection(frch)
# with open('camargue-macon-sanremo-frch.geojson', 'w') as f: f.write(json.dumps(mapping(tilefrch)))

# "Eat" into france by taking the italian side and growing it (`buffer`)
walps_it = walps.difference(frch)
# Note that geoms]0
frch_buff = tilefrch.difference(walps_it.buffer(0.001)).geoms[0]
with open('camargue-macon-sanremo-frch-eaten.geojson', 'w') as f: f.write(json.dumps(mapping(frch_buff)))

```


Merge the results
-----------------

We'll use a few helpers in <a href='./geo/src/mbtidime/mbtshell.sh'>mbtshell.sh</a>

There are two handy functions to merge MBTiles. The first one does not handle conflicts, and neither update the bounds.


***Note*: jpeg quality**

* SwissTopo uses Quality: 88
* Bugianen uses Quality: 80
* IGN uses Quality: 75 (also gdal's default)

be careful to use a higher quality for the merge, to minimize jpeg double-compression artifacts.

