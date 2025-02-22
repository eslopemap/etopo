The idea is to provide both hiking, cycling and skiing maps back by the same vector data:

* Hiking and cyling styles are already provided by the OpenAndroMaps Elevate theme
* For winter, 
  * all paths can be toned down
  * ski slopes can be highlighted (like https://openskimap.org does)
  * ground appearance (forest, farmland, scree, glacier...) should be styled
    in a way that interferes as little as possible with the slop overlay
  * details can be shown at lower zoom levels as skiing happen in sparsely populated areas.
  * hill-shading layer hidden
  * the slopes are added with a multiplicative (rather), transparent overlay

In table form:

| Style   →<br> Elements↓ | Summer                         | Winter           |
|-------------------------|--------------------------------|------------------|
| Path                    | colored by hike  or bike grade | dim/grey         |
| Ski slope               | dim                            | colored by grade |
| Forest                  | green+motif                    | icon             |
| Other ground            | color+motif                    | icons            |
| Contour lines           | ✓                              | ✓✓               |
| Hill shading raster ovl | ✓                              | ✕                |
| Slope raster ovl        | ✕                              | ✓                |

This would be available ideally on Android, Web, and Desktop, taking advantage of the existing ecosystem (see [State of the art](vector-topo-sota.md))


# First steps

* Take a look at existing formats, starting with MVT
  * Try to display a tile in a notebook. See [pymgl](https://github.com/brendan-ward/pymgl)
   and [Inspecting MBTiles in Python](https://python.plainenglish.io/debugging-mbtiles-in-python-8f4db8fbeacc),
   also [mapbox-gl-to-blob](https://github.com/mapparatus/mapbox-gl-to-blob)
  * if it's too hard to install them, [mbgl-renderer](https://github.com/consbio/mbgl-renderer) has a docker build with a REST server.
* experiment with the awesome [Maputnik](https://openmaptiles.org/docs/style/maputnik/) or [Fresco](https://github.com/go-spatial/fresco) (react):
  * try to add some POI features from the other styles to [MapTiler Terrain](https://openmaptiles.org/styles/) to make the summer map.
  * try to make a SwissTopo style
* try to figure out if there are more capabilities in mapforge styles / how to convert between the 2
