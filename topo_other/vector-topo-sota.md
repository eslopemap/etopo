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
* PBF

## Frontend

* Javascript:
  * [Mapbox.js](https://blog.mapbox.com/announcing-mapbox-js-1-0-with-leaflet-b424decceaf6)
  * MapLibre GL JS - [Add a vector tile source](https://maplibre.org/maplibre-gl-js-docs/example/vector-source/)
* Java
  * Mapsforge VTM handles both MVT/MBTiles and mapsforge (and more geojson...) ; and supports render themes
* OpenAndroMap

It would be interesting to compare styling approaches amongst 
* [mapsforge/vtm/Rendertheme](https://github.com/mapsforge/vtm/blob/master/docs/Rendertheme.md)
  * eg provided by OpenAndroMaps *[Elevate](openandromaps.org/en/legend/elevate-mountain-hike-theme)* theme
  * ...and supported by many [applications](https://github.com/mapsforge/mapsforge/blob/master/docs/Mapsforge-Applications.md)
    * notably Android: OruxMaps,
    * and linux: Cruiser
* [MapTiler – OpenMapTiles open styles](https://openmaptiles.org/styles/) == [Mapbox GL style specification](https://openmaptiles.org/docs/style/mapbox-gl-style-spec/)
* OpenAndromaps xml

## Improvements needed

* Compute more precise elevation contour lines, and save in a compact vector format, but with higher vector precision than the current default available in Organic maps / OpenAndroMaps.

# Map tooling on linux

## Pure maps

PureMaps integrates out-of-the-box with:
* MapTiler Vector & raster (satellite) data. The "terrain" mode, customized from [upstream](https://openmaptiles.org/styles/#maptiler-terrain) (additional hiking trail colors & POI) provides a good outdoor map.
* OpenTopoMap (raster)
* HERE and Mapbox, with API key

### Technical

* [written](https://github.com/rinigus/pure-maps) in QML/python/C++
* uses [rinigus/mapbox-gl-qml: Unofficial Mapbox GL Native bindings for Qt QML](https://github.com/rinigus/mapbox-gl-qml)

### Install
It is packaged as [a flatpak](https://flathub.org/apps/details/io.github.rinigus.PureMaps):

```sh
flatpak install --user https://flathub.org/repo/appstream/io.github.rinigus.PureMaps.flatpakref
```

## mapsforge: Cruiser

```sh
/usr/lib/jvm/java-8-openjdk-amd64/jre/bin/java -Xmx1024M -jar cruiser-gl.jar
```

## overlay multiply transparency: AlpineQuest

on Ubuntu 22.04:

```sh

snap install --devmode --beta anbox
sudo apt install android-tools-adb

```
