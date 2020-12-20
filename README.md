# Rendering paper maps from tiles using Landez and Mapnik

This program renders an area with given boundaries using tiles from either a [mapbox MBTiles file](https://wiki.openstreetmap.org/wiki/MBTiles), a [tile server](https://wiki.openstreetmap.org/wiki/Tile_servers) or locally rendered using [mapnik](http://mapnik.org/). It is designed to work with hikingmap but it can be used standalone as well if desired.

## Installation
Clone this repository and run the following command in the created directory.
```bash
python setup.py install
```

## Usage

`hm-render-landez [OPTION]... [gpxfiles]... bbox|center ...`

Options:

| Parameter | Description
| --------- | -----------
| `--pagewidth` | Page width in cm
| `--pageheight` | Page height in cm
| `-b, --basename` | Base filename without extension
| `-t` | Temp track file to render. This is used by hikingmap to draw the page boundaries of the overview map, the tracks will be saved as a temporary GPX file.
| `-y` | Temp waypoints file to render. This is used by hikingmap to render the distance each kilometer or mile, the waypoints will be saved as a temporary GPX file.
| `-v, --verbose` | Display extra information while processing.
| `-h, --help` | Display help
| `-d, --dpi` | Amount of detail to render in dots per inch, default 300
| `-S, --scale-factor` | Scale factor, default 1.0
| `--hikingmapstyle` | Hikingmap stylesheet file, contains the CartoCSS for the tracks and the waypoints. The default is hikingmapstyle.xml, see the repository for an example.
| `-f, --format` | Output format. Consult the mapnik documentation for possible values, default png
| `--mbtiles` | Input raster mbtiles file
| `--mapnik-style` | Mapnik stylesheet file
| `--wmts-url` | Remote URL to download tiles
| `--wmts-subdomains` | URL subdomains
| `--cachedir` | Local folder containing cached tiles, will be placed in the system temp directory if not specified
| `--tilesize` | Tile size, default 256
| `--tileformat` | Tile image format, default image/png
| `--tilescheme` | Tile scheme, default wmts
| `gpxfiles` | The GPX track(s) to render.

You should at least specify one tile source, read the section about [tile source precedence](#tile-source-precedence) for detailed information.
After these parameters you are required to make a choice between bbox and center. In bbox mode the rendered area will be a defined bounding box and in center mode you can specify a center coordinate and a scale.

Options for bbox mode:

| Parameter | Description
| --------- | -----------
| `-o, --minlon` | Minimum longitude of the page
| `-O, --maxlon` | Maximum longitude of the page
| `-a, --minlat` | Minimum latitude of the page
| `-A, --maxlat` | Maximum latitude of the page

Note that mapnik will maintain the aspect ratio, the rendered area may not correspond exactly to the given boundary.

Options for center mode:

| Parameter | Description
| --------- | -----------
| `--lon` | Longitude of the center of the page
| `--lat` | Latitude of the center of the page
| `--scale` | Scale denominator, default 50000

## Configuration file

Because most of the time you will want to use the same parameters, you can optionally override the defaults in a configuration file. hm-render-landez will search for a file hm-render-landez.config.xml in the current directory, if not found it will resort to ~/.hm-render-landez.config.xml

```
<?xml version="1.0" encoding="utf-8"?>
<hm-render-landez>
    <tilesmanager>
        <mbtiles_file>mbsource.mbtiles</mbtiles_file>
        <mapnik_stylefile>mapnik_style.xml</mapnik_stylefile>
        <wmts_url>https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png</wmts_url>
        <wmts_subdomains>abc</wmts_subdomains>
        <cache_dir>tilecache</cache_dir>
        <tile_size>256</tile_size>
        <tile_format>image/png</tile_format>
        <tile_scheme>wmts</tile_scheme>
    </tilesmanager>
    <hikingmapstyle>hikingmap_style.xml</hikingmapstyle>
    <outputformat>png</outputformat>
    <dpi>300</dpi>
    <scalefactor>1.0</scalefactor>
    <fontdirs>
        <fontdir>/usr/share/fonts/noto</fontdir>
        <fontdir>/usr/share/fonts/noto-cjk</fontdir>
        <fontdir>/usr/share/fonts/TTF</fontdir>
    </fontdirs>
</hm-render-landez>
```

Options:

| Tag | Description
| --- | -----------
| mbtiles_file | Optional. An MBTiles file providing raster tiles.
| mapnik_stylefile | Optional. Mapnik stylesheet file.
| wmts_url | Optional. Remote URL to download tiles.
| wmts_subdomains | Optional. URL subdomains.
| cache_dir | Local folder containing cached tiles.
| tile_size | Tile size.
| tile_format | Tile image format.
| tile_scheme | Tile scheme, value can be tms or wmts.
| hikingmapstyle | Hikingmap stylesheet file, contains the CartoCSS for the tracks and the waypoints, see the repository for an example.
| outputformat | Output format. Consult the [mapnik documentation](http://mapnik.org/docs/v2.2.0/api/python/mapnik._mapnik-module.html#render_to_file) for possible values.
| dpi | Amount of detail to render in dots per inch. This value is unrelated to the setting on your printer, a higher value will simply result in smaller icons, thinner roads and unreadable text.
| scalefactor | The scale factor to compensate for a higher dpi value.
| fontdirs | Optional. Can contain one or more fontdir subtags with additional font directories to be used by mapnik.

## Prerequisites

To run this script you should have a working installation of [python 3](https://www.python.org/), [Landez](https://github.com/makinacorpus/landez) and [mapnik](http://mapnik.org/). Make sure you also have [python-mapnik](https://github.com/mapnik/python-mapnik/) installed.

## Tile sources

The tiles are cached in a local folder using the tile manager of Landez. Landez will add tiles to the cache when necessary, supporting a number of possible sources.

### MBTiles

This is a file format from mapbox, they can be created using tools such as (but not limited to) [mapbox mbutil](https://github.com/mapbox/mbutil) or [Maperitive](http://maperitive.net/). Please note that only raster MBTiles files are supported, vector MBTiles files require rendering before use.

### Tile server

This is the easiest to set up, Landez will simply download tiles from a web source. Make sure you don't violate [usage policies](https://operations.osmfoundation.org/policies/tiles/) if you render too many maps at once or set the dpi value too high.

### Local rendering with mapnik

Since mapnik is installed as a prerequisite of this project, it is included as a possible tile source. However the setup is rather difficult. Consult the documentation of [hm-render-mapnik](https://github.com/roelderickx/hm-render-mapnik/) to get an idea.

### WMS server

Although Landez supports WMS sources, it is not configurable here. WMS servers are generally replaced by WMTS servers, which use fewer resources on the server side.

## Tile source precedence

Please note you should at least specify one tile source. Although it is possible to pass all tile sources together, Landez will use only one of them. The precedence is:
1. MBTiles, pass the parameter `--mbtiles` if you want to use this.
2. Mapnik, pass the parameter `--mapnik-style` if you want to use this, but don't pass `--mbtiles`.
3. Tile server, pass the parameters `--wmts-url` and `--wmts-subdomains`, but don't pass `--mbtiles` and `--mapnik-style`.

