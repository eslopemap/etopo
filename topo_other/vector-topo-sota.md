# Vector map ecosystem:


## Companies

**Mapbox** provided open-source libraries but after a license change, they were forked by **MapTiler** into MapLibre.
![image](https://user-images.githubusercontent.com/2772505/192139572-34684525-62d7-43a9-ad41-2dd55b7b2f46.png)
MapTiler also maintains [tileserver-gl](https://github.com/maptiler/tileserver-gl) (javascript

## Data

* MapTiler ["OSM Planet" tiles](https://data.maptiler.com/downloads/dataset/osm/) weigh < 100Gb, use "[OpenMapTiles](https://github.com/openmaptiles/openmaptiles)" Open vector tile schema
* [OpenAndroMaps](https://www.openandromaps.org/) offers downloads of both 
[raster](https://www.openandromaps.org/en/downloads/general-maps) (for low zoom levels), 
and vector maps using mapsforge space-optimized format.
* API-Key-only online: [Thunderforest](https://www.thunderforest.com/docs/vector-maps-api/) MVT [Outdoors(https://www.thunderforest.com/docs/thunderforest.outdoors-v2/) ([raster version](https://www.thunderforest.com/maps/outdoors/))

## Formats:
* [Mapbox Vector Tiles]([url](https://docs.mapbox.com/data/tilesets/guides/vector-tiles-standards/)) MVT (PBF-based, used in MBTiles too)
  * also used by OpenMapTiles / https://github.com/mapbox/vector-tile-spec
* OBF: [OsmAnd Binary Maps - .obf](https://osmand.net/docs/technical/osmand-file-formats/osmand-obf)

### Styles

2 main competing approaches. mapsforge is geared towards mobile/offline/java wheras MVT with Mapbox GL styling & derivatives is built around tiling, C++ & web, with larger support by Gdal, protomaps, ... and corporate backing by Mapbox, Maptiler, Felt. So it feels like the place to start.

It would be interesting to compare styling approaches amongst 
* [mapsforge/vtm/Rendertheme](https://github.com/mapsforge/vtm/blob/master/docs/Rendertheme.md)
  * eg provided by OpenAndroMaps *[Elevate](openandromaps.org/en/legend/elevate-mountain-hike-theme)* theme
  * ...and supported by many [applications](https://github.com/mapsforge/mapsforge/blob/master/docs/Mapsforge-Applications.md)
    * notably Android: OruxMaps,
    * and linux: Cruiser
  * unfortunately [web](https://github.com/mapsforge/vtm/blob/master/docs/web.md) support is through JWT.
* [MapTiler – OpenMapTiles open styles](https://openmaptiles.org/styles/) == [Mapbox GL style specification](https://openmaptiles.org/docs/style/mapbox-gl-style-spec/)
  * used eg by Pure Maps (presumably) for their terrain theme.
  * unlike mapsforge, currently no frontends allow the end-user to show/hide elements
* OsmAnd [Map Rendering style - .render.xml](https://osmand.net/docs/technical/osmand-file-formats/osmand-rendering-style)
* [Organic Maps](https://github.com/organicmaps/organicmaps) seems to have an in-house approach that also includes a topo style.

## Frontend

* Javascript:
  * [Mapbox.js](https://blog.mapbox.com/announcing-mapbox-js-1-0-with-leaflet-b424decceaf6)
  * MapLibre GL JS - [Add a vector tile source](https://maplibre.org/maplibre-gl-js-docs/example/vector-source/)
* Java
  * Mapsforge VTM handles both MVT/MBTiles and mapsforge (and more geojson...) ; and supports render themes
* OpenAndroMap

## Improvements needed

* Compute more precise elevation contour lines, and save in a compact vector format, but with higher vector precision than the current default available in Organic maps / OpenAndroMaps.

# Map tooling on linux

#### Pure maps

PureMaps integrates out-of-the-box with:
* MapTiler Vector & raster (satellite) data. The "terrain" mode, customized from [upstream](https://openmaptiles.org/styles/#maptiler-terrain) (additional hiking trail colors & POI) provides a good outdoor map.
* OpenTopoMap (raster)
* HERE and Mapbox, with API key

##### Technical

* [written](https://github.com/rinigus/pure-maps) in QML/python/C++
* uses [rinigus/mapbox-gl-qml: Unofficial Mapbox GL Native bindings for Qt QML](https://github.com/rinigus/mapbox-gl-qml)

##### Install
It is packaged as [a flatpak](https://flathub.org/apps/details/io.github.rinigus.PureMaps):

```sh
flatpak install --user https://flathub.org/repo/appstream/io.github.rinigus.PureMaps.flatpakref
```

#### mapsforge: Cruiser

```sh
/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java -Xmx1024M -jar cruiser-gl.jar
```

#### Organic Maps

Oe of the best integrated solutions for OSM-based offline navigation on mobile. Includes a custom topo style which is quite good.

[on Github](https://github.com/organicmaps/organicmaps) / [on Flathub](https://flathub.org/apps/details/app.organicmaps.desktop)

```sh
flatpak install https://dl.flathub.org/repo/appstream/app.organicmaps.desktop.flatpakref
```

Installing as an Android app (as below) will likely gain you 1Gb of disk space.

#### Using Android apps

[AlpineQuest](https://www.alpinequest.net/) supports only raster maps but it has the best custom map & overlay support of any platform, so it's a good baseline.
on Ubuntu 22.04:

```sh
snap install --devmode --beta anbox
sudo apt install android-tools-adb
anbox session-manager &
sleep 30
anbox.appmgr
adb devices  # shows emulator-XXXX
adb install ~/Downloads/android/AlpineQuest_2.2.8.r6676.apk
# now AlpineQuest is shown in AppMgr
```
