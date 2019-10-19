# Rendering paper maps using tiles

This script renders an area with given boundaries using tiles from either a [mapbox MBTiles file](https://wiki.openstreetmap.org/wiki/MBTiles), a [tile server](https://wiki.openstreetmap.org/wiki/Tile_servers) or locally rendered using [mapnik](http://mapnik.org/). It is designed to work with hikingmap but it can be used standalone as well if desired.

## Usage

`render.py [OPTION]... gpxfiles...`

Options:

| Parameter | Description
| --------- | -----------
| `-o` | Minimum longitude of the area boundaries
| `-O` | Maximum longitude of the area boundaries
| `-a` | Minimum latitude of the area boundaries
| `-A` | Maximum latitude of the area boundaries
| `-w` | Page width in cm
| `-h` | Page height in cm
| `-t` | Temp track file to render. This is used to draw the page boundaries of the overview map, hikingmap will save those as a temporary GPX file.
| `-y` | Temp waypoints file to render. This is used to render the distance each kilometer or mile, hikingmap will save those waypoints as a temporary GPX file.
| `-v, --verbose` | Display extra information while processing.
| `-h, --help` | Display help
| `gpxfiles` | The GPX track(s) to render.

## Prerequisites

To run this script you should have a working installation of [python 3](https://www.python.org/), [Landez](https://github.com/makinacorpus/landez) and [mapnik](http://mapnik.org/). Make sure you also have [python-mapnik](https://github.com/mapnik/python-mapnik/) installed.

## Tile sources

The tiles are cached in a local folder using the tile manager of Landez. Landez will add tiles to the cache when necessary, supporting a number of possible sources.

### MBTiles

This is a file format from mapbox, they can be created using tools such as (but not limited to) [mapbox mbutil](https://github.com/mapbox/mbutil) or [Maperitive](http://maperitive.net/). Please note that only raster MBTiles files are supported, vector MBTiles files require rendering before use.

### Tile server

This is the easiest to set up, Landez will simply download tiles from a web source. Make sure you don't violate [usage policies](https://operations.osmfoundation.org/policies/tiles/) if you render too many maps at once or set the dpi value too high.

### Mapnik

Since mapnik is installed as a prerequisite of this project, it is included as a possible tile source. However the setup is rather difficult. Consult the documentation of [render_mapnik](https://github.com/roelderickx/hikingmap/blob/master/documentation/render_mapnik.html) in the hikingmap package to get an idea.

### WMS server

Although Landez supports WMS sources, it is not configurable here. WMS servers are generally replaced by WMTS servers, which use fewer resources on the server side.

## Configuration

Apart from these parameters there are some specific parameters for this renderer. They need to be configured in the file render_tiles.config.xml. An example is included in this repository:

```
<?xml version="1.0" encoding="utf-8"?>
<render_tiles>
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
</render_tiles>
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
| hikingmapstyle | The filename of the hikingmap stylesheet. This stylesheet contains the styles to draw the GPX track and waypoints.
| outputformat | Output format. See the [mapnik documentation](http://mapnik.org/docs/v2.2.0/api/python/mapnik._mapnik-module.html#render_to_file) for possible values.
| dpi | Amount of detail to render in dots per inch. This value is unrelated to the setting on your printer, a higher value will simply result in smaller icons, thinner roads and unreadable text.
| scalefactor | The scale factor to use when rendering to image formats.
| fontdirs | Optional. Can contain one or more fontdir subtags with additional font directories to be used by mapnik.

### Tile source precedence

Please note you should at least add one tile source. Although it is possible to define all tile sources together in &lt;tilesmanager&gt;, Landez will use only one of them. The precedence is:
1. MBTiles. Fill the tag &lt;mbtiles_file&gt; if you want to use this.
2. Mapnik. Fill the tag &lt;mapnik\_stylefile&gt; if you want to use this, but leave &lt;mbtiles\_file&gt; blank or remove this tag.
3. Tile server. Fill the tags &lt;wmts\_url&gt; and &lt;wmts_subdomains&gt; if you want to use this, but leave &lt;mbtiles\_file&gt; and &lt;mapnik\_stylefile&gt; blank or remove them.

