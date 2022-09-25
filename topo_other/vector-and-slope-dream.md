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
