## Notice
That's my fork for optimising label-maker for Google Colab
I add argument `-mbtiles` for `label-maker labels` command



# Label Maker
## Data Preparation for Satellite Machine Learning

Label Maker downloads [OpenStreetMap QA Tile]((https://osmlab.github.io/osm-qa-tiles/)) information and satellite imagery tiles and saves them as an [`.npz` file](https://docs.scipy.org/doc/numpy/reference/generated/numpy.savez.html) for use in machine learning training.

![example classification image overlaid over satellite imagery](examples/images/classification.png)
_satellite imagery from [Mapbox](https://www.mapbox.com/) and [Digital Globe](https://www.digitalglobe.com/)_

## Requirements
- [Python 3.6](https://www.python.org/)
- [tippecanoe](https://github.com/mapbox/tippecanoe)

## Installation

```bash
!git clone https://github.com/NickElixir/label-maker.git
os.chdir("label-maker")
!python setup.py install
```

Note that running this library this requires `tippecanoe` as a "peer-dependency" and that command should be available from your command-line before running this.

## Documentation

Full author's documentation is available here: http://devseed.com/label-maker/

## Acknowledgements from @Drewbo

This library builds on the concepts of [skynet-data](https://github.com/developmentseed/skynet-data). It wouldn't be possible without the excellent data from OpenStreetMap and Mapbox under the following licenses:
- OSM QA tile data [copyright OpenStreetMap contributors](http://www.openstreetmap.org/copyright) and licensed under [ODbL](http://opendatacommons.org/licenses/odbl/)
- Mapbox Satellite data can be [traced for noncommercial purposes](https://www.mapbox.com/tos/#[YmtMIywt]).

It also relies heavily on Marc Farra's [tilepie](https://github.com/kamicut/tilepie) to asynchronously process vector tiles
