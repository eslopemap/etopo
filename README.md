# eTopo: Enhanced topo maps

This repo contains the following folders:


### `src`

Supporting code, from low- to higher-level dependencies.

* [img_util.py](src/img_util.py): detecting partial tiles ; merging them ; and "tiling" them
* [mbt_pyramid.py](src/mbt_pyramid.py): assemble mbtiles samples at each zoom-level in a grid
* [mbt_download.py](src/mbt_download.py): download tiles, possibly into mbtiles
* [mbt_partial.py](src/mbt_partial.py): massive cleanup of mbtiles using the above

⚠️ This code depends on [eslope libs], which are not packaged.


### topo compare

Visual comparison of different topo maps covering overlapping areas.

* [202112-topomap-fr-it.ipynb]: focused on western alps, IGN, SwissTopo
* [202112-topo-map-graphics-comparison.ipynb]: on central-alps, with a wider array of maps incl. kompass.


### topo merge

Merge different topo maps to play to the strengh of each, in order to eventually cover most of the alps.
The tile download is usually done with external tools (MOBAC).

<!-- * [202012-Offline-SwissTopo.md] -->
* [202102-Alps-Topo.md]: Currently only contains the fr(ign) + it(Bugianen) merge, following the exact border.
* [202112-SwissTopo.ipynb]: download SwissTopo base layer, starting with downsampled tiles and filling missing data with the "big" tiles. These 2 explain some of the code used:
  + [202112-explore-SwissTopo-partial-detect.ipynb]: how to detect partial tiles ie missing part of the image.
  + [202112-explore-SwissTopo-partial-merge.ipynb]: how to fill missing content in a tile.
* [202111-Bugianen-merge.ipynb]: tiny one, to merge all Bugianen mbtiles maps


### topo other

* [202111-piemonte-CTR-steep-only.ipynb]: An experiment to see if I could extract only cliff contours from the Italina piemonte CTR _(Carta Tecnica Regionale)_. Not conclusive, but kept for the scikit-image examples.


_Note: Notebook links use the great nbviewer.org_

<!-- Links: -->
[eslope libs]:https://github.com/eslopemap/eslope/tree/main/development/src
[202112-topomap-fr-it.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_compare/202112-topomap-fr-it.ipynb
[202112-topo-map-graphics-comparison.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_compare/202112-topo-map-graphics-comparison.ipynb
[202012-Offline-SwissTopo.md]:topo_download/202012-Offline-SwissTopo.md
[202111-Bugianen-merge.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_download/202111-Bugianen-merge.ipynb
[202112-SwissTopo.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_download/202112-SwissTopo.ipynb
[202102-Alps-Topo.md]:https://nbviewer.org/github/eslopemap/etopo/blob/main/
[202112-explore-SwissTopo-partial-detect.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_merge/202112-explore-SwissTopo-partial-detect.ipynb
[202112-explore-SwissTopo-partial-merge.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_merge/202112-explore-SwissTopo-partial-merge.ipynb
[202111-piemonte-CTR-steep-only.ipynb]:https://nbviewer.org/github/eslopemap/etopo/blob/main/topo_other/202111-piemonte-CTR-steep-only.ipynb
[]:https://nbviewer.org/github/eslopemap/etopo/blob/main/
