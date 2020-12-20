#!/usr/bin/env python3

# hm-render-landez -- render maps on paper using tiles with landez and mapnik
# Copyright (C) 2019  Roel Derickx <roel.derickx AT gmail>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os, argparse, math, mapnik
from xml.dom import minidom
from landez import TilesManager, GoogleProjection, ExtractionError

# global constants
earthCircumference = 40041.44 # km (average, equatorial 40075.017 km / meridional 40007.86 km)
cmToKmFactor = 100000.0
inch = 2.54 # cm

def search_configfile():
    filename = 'hm-render-landez.config.xml'
    if os.path.exists(filename):
        return os.path.abspath(filename)
    elif os.path.exists(os.path.join(os.path.expanduser('~'), '.' + filename)):
        return os.path.join(os.path.expanduser('~'), '.' + filename)
    else:
        return None


def get_xml_subtag_value(xmlnode, sublabelname):
    elements = xmlnode.getElementsByTagName(sublabelname)
    return str(elements[0].firstChild.nodeValue) if elements and elements[0].childNodes else None


def parse_configfile():
    config = {}
    config['hikingmapstyle'] = 'hikingmap_style.xml'
    config['output_format'] = 'png'
    config['dpi'] = 300
    config['scale_factor'] = 1.0
    config['tilesize'] = 256
    config['tileformat'] = 'image/png'
    config['tilescheme'] = 'wmts'

    configfile = search_configfile()
    
    if configfile:
        xmldoc = None
        xmlmapnik = None
        
        try:
            xmldoc = minidom.parse(configfile)
        except:
            pass
        
        if xmldoc:
            xmllandez_element = xmldoc.getElementsByTagName('hm-render-landez')
            if xmllandez_element:
                xmllandez = xmllandez_element[0]
        
        if xmllandez:
            xmltilesmanagerlist = xmllandez.getElementsByTagName('tilesmanager')
            if xmltilesmanagerlist:
                xmltilesmanager = xmltilesmanagerlist[0]
                
                mbtilesfile = get_xml_subtag_value(xmltilesmanager, 'mbtiles_file')
                if mbtilesfile:
                    config['mbtilesfile'] = mbtilesfile
                
                mapnikstyle = get_xml_subtag_value(xmltilesmanager, 'mapnik_stylefile')
                if mapnikstyle:
                    config['mapnikstyle'] = mapnikstyle
                
                wmtsurl = get_xml_subtag_value(xmltilesmanager, 'wmts_url')
                if wmtsurl:
                    config['wmtsurl'] = wmtsurl
                
                wmtssubdomains = get_xml_subtag_value(xmltilesmanager, 'wmts_subdomains')
                if wmtssubdomains:
                    config['wmtssubdomains'] = wmtssubdomains
                
                cachedir = get_xml_subtag_value(xmltilesmanager, 'cache_dir')
                if cachedir:
                    config['cachedir'] = cachedir
                
                tilesize = get_xml_subtag_value(xmltilesmanager, 'tile_size')
                if tilesize:
                    config['tilesize'] = int(tilesize)
                
                tileformat = get_xml_subtag_value(xmltilesmanager, 'tile_format')
                if tileformat:
                    config['tileformat'] = tileformat
                
                tilescheme = get_xml_subtag_value(xmltilesmanager, 'tile_scheme')
                if tilescheme:
                    config['tilescheme'] = tilescheme
            
            hikingmapstyle = get_xml_subtag_value(xmllandez, 'hikingmapstyle')
            if hikingmapstyle:
                config['hikingmapstyle'] = hikingmapstyle
            
            output_format = get_xml_subtag_value(xmllandez, 'outputformat')
            if output_format:
                config['output_format'] = output_format
            
            dpi = get_xml_subtag_value(xmllandez, 'dpi')
            if dpi:
                config['dpi'] = int(dpi)
            
            scale_factor = get_xml_subtag_value(xmllandez, 'scalefactor')
            if scale_factor:
                config['scale_factor'] = float(scale_factor)
            
            xmlfontdirs = xmlmapnik.getElementsByTagName('fontdirs')
            if xmlfontdirs:
                xmlfontdirlist = xmlfontdirs[0].getElementsByTagName('fontdir')
                for xmlfontdir in xmlfontdirlist:
                    if xmlfontdir and xmlfontdir.childNodes:
                        fontdir = str(xmlfontdir.firstChild.nodeValue)
                        if fontdir:
                            mapnik.FontEngine.register_fonts(fontdir, True)
    
    return config


def parse_commandline():
    config = parse_configfile()

    parser = argparse.ArgumentParser(description = "Render a map on paper using mapnik")
    parser.add_argument('--pagewidth', dest = 'pagewidth', type = float, default = 20.0, \
                        help = "page width in cm")
    parser.add_argument('--pageheight', dest = 'pageheight', type = float, default = 28.7, \
                        help = "page height in cm")
    parser.add_argument('-b', '--basename', dest = 'basefilename', default = "detail", \
                        help = "base filename without extension")
    parser.add_argument('-t', dest = 'temptrackfile', \
                        help = "temp track file to render")
    parser.add_argument('-y', dest = 'tempwaypointfile', \
                        help = "temp waypoints file to render")
    parser.add_argument('-v', dest = 'verbose', action = 'store_true')
    # hm-render-landez specific parameters
    parser.add_argument('-d', '--dpi', type=int, default=config['dpi'], \
                        help = "amount of detail to render in dots per inch (default: %(default)s)")
    parser.add_argument('-S', '--scale-factor', type=float, default=config['scale_factor'], \
                        help = "scale factor (default: %(default)s)")
    parser.add_argument('--hikingmapstyle', default=config['hikingmapstyle'], \
                        help = "hikingmap stylesheet file, contains the CartoCSS for " + \
                               "the tracks and the waypoints (default: %(default)s)")
    parser.add_argument('-f', '--format', dest='output_format', default=config['output_format'], \
                        help = "output format, consult the mapnik documentation for " + \
                               "possible values (default: %(default)s)")
    parser.add_argument('--mbtiles', dest='mbtiles_file', \
                        default=config['mbtilesfile'] if 'mbtilesfile' in config else None, \
                        help = "input raster mbtiles file")
    parser.add_argument('--mapnik-style', dest='mapnik_stylefile', \
                        default=config['mapnikstyle'] if 'mapnikstyle' in config else None, \
                        help = "mapnik stylesheet file")
    parser.add_argument('--wmts-url', dest='wmts_url', \
                        default=config['wmtsurl'] if 'wmtsurl' in config else None, \
                        help = "remote URL to download tiles")
    parser.add_argument('--wmts-subdomains', dest='wmts_subdomains', \
                        default=config['wmtssubdomains'] if 'wmtssubdomains' in config else None, \
                        help = "URL subdomains")
    parser.add_argument('--cachedir', dest='cache_dir', \
                        default=config['cachedir'] if 'cachedir' in config else None, \
                        help = "local folder containing cached tiles")
    parser.add_argument('--tilesize', type=int, default=config['tilesize'], dest='tile_size', \
                        help = "tile size")
    parser.add_argument('--tileformat', default=config['tileformat'], dest='tile_format', \
                        help = "tile image format")
    parser.add_argument('--tilescheme', choices=[ 'tms', 'wmts' ], default=config['tilescheme'], \
                        dest='tile_scheme', help = "tile scheme")
    # --
    parser.add_argument('gpxfiles', nargs = '*')
    
    subparsers = parser.add_subparsers(dest='mode', required=True, \
                                       help='bounding box or center mode')
    
    # create the parser for the bbox command
    parser_bbox = subparsers.add_parser('bbox', help='define bounding box')
    parser_bbox.add_argument('-o', '--minlon', type=float, required = True, \
                        help = "minimum longitude")
    parser_bbox.add_argument('-O', '--maxlon', type=float, required = True, \
                        help = "maximum longitude")
    parser_bbox.add_argument('-a', '--minlat', type=float, required = True, \
                        help = "minimum latitude")
    parser_bbox.add_argument('-A', '--maxlat', type=float, required = True, \
                        help = "maximum latitude")

    # create the parser for the atlas command
    parser_atlas = subparsers.add_parser('center', help='define center mode')
    parser_atlas.add_argument('--lon', type=float, required=True, \
                              help='longitude of the center of map')
    parser_atlas.add_argument('--lat', type=float, required=True, \
                              help='latitude of the center of map')
    parser_atlas.add_argument('--scale', type=int, default=50000, \
                              help='scale denominator')

    return parser.parse_args()


def convert_cm_to_degrees_lon(lengthcm, scale, latitude):
    lengthkm = lengthcm / cmToKmFactor * scale
    return lengthkm / ((earthCircumference / 360.0) * math.cos(math.radians(latitude)))


def convert_cm_to_degrees_lat(lengthcm, scale):
    lengthkm = lengthcm / cmToKmFactor * scale
    return lengthkm / (earthCircumference / 360.0)


def assure_bbox_mode(parameters):
    if parameters.mode == 'center':
        pagesize_lon = convert_cm_to_degrees_lon(parameters.pagewidth, \
                                                 parameters.scale, parameters.lat)
        pagesize_lat = convert_cm_to_degrees_lat(parameters.pageheight, parameters.scale)
        
        parameters.minlon = parameters.lon - pagesize_lon / 2
        parameters.minlat = parameters.lat - pagesize_lat / 2
        parameters.maxlon = parameters.lon + pagesize_lon / 2
        parameters.maxlat = parameters.lat + pagesize_lat / 2

    
def create_tiles_manager(parameters):
    tm_args = { }
    tm_args['cache'] = True
    if parameters.mbtiles_file:
        tm_args['mbtiles_file'] = parameters.mbtiles_file
    if parameters.wmts_url:
        tm_args['tiles_url'] = parameters.wmts_url
        tm_args['tiles_headers'] = { }
        tm_args['tiles_headers']['User-Agent'] = 'hikingmap/render_tiles'
        tm_args['tiles_headers']['Accept'] = 'image/png,image/*;q=0.9,*/*;q=0.8'
    if parameters.wmts_subdomains:
        tm_args['tiles_subdomains'] = parameters.wmts_subdomains
    if parameters.mapnik_stylefile:
        tm_args['stylefile'] = parameters.mapnik_stylefile
    if parameters.cache_dir:
        tm_args['tiles_dir'] = parameters.cache_dir
    if parameters.tile_size:
        tm_args['tile_size'] = parameters.tile_size
    if parameters.tile_format:
        tm_args['tile_format'] = parameters.tile_format
    if parameters.tile_scheme:
        tm_args['tile_scheme'] = parameters.tile_scheme
    
    tm = TilesManager(**tm_args)
    
    return tm


def latRad(lat):
    sin = math.sin(math.radians(lat))
    radX2 = math.log((1 + sin) / (1 - sin)) / 2
    return max(min(radX2, math.pi), -math.pi) / 2


def zoom(mapPx, worldPx, fraction):
    return math.floor(math.log(mapPx / worldPx / fraction, 2))


def calc_zoomlevel(pagewidth, pageheight, dpi, scalefactor, tilesize, \
                   minlon, minlat, maxlon, maxlat):
    px_width = (pagewidth * dpi / inch) / scalefactor
    px_height = (pageheight * dpi / inch) / scalefactor
    
    lat_fraction = (latRad(maxlat) - latRad(minlat)) / math.pi
    lon_fraction = maxlon - minlon
    if lon_fraction < 0:
        lon_fraction += 360
    lon_fraction /= 360
    
    lat_zoom = zoom(px_height, tilesize, lat_fraction)
    lon_zoom = zoom(px_width, tilesize, lon_fraction)

    return [ min(lat_zoom, lon_zoom) ]


def render(parameters):
    if not parameters.verbose:
        mapnik.logger.set_severity(getattr(mapnik.severity_type, 'None'))

    merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')
    longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

    imgwidth = math.trunc(parameters.pagewidth / inch * parameters.dpi)
    imgheight = math.trunc(parameters.pageheight / inch * parameters.dpi)

    m = mapnik.Map(imgwidth, imgheight)
    #mapnik.load_map(m, parameters.mapstyle)
    mapnik.load_map(m, parameters.hikingmapstyle)
    m.srs = merc.params()

    if hasattr(mapnik, 'Box2d'):
        bbox = mapnik.Box2d(parameters.minlon, parameters.minlat, parameters.maxlon, parameters.maxlat)
    else:
        bbox = mapnik.Envelope(parameters.minlon, parameters.minlat, parameters.maxlon, parameters.maxlat)

    transform = mapnik.ProjTransform(longlat, merc)
    merc_bbox = transform.forward(bbox)
    m.zoom_to_box(merc_bbox)

    # create raster symbolizer / rule / style
    rastersymbolizer = mapnik.RasterSymbolizer()
    rastersymbolizer.opacity = 1.0
    rasterrule = mapnik.Rule()
    rasterrule.symbols.append(rastersymbolizer)
    rasterstyle = mapnik.Style()
    rasterstyle.rules.append(rasterrule)
    m.append_style('RasterStyle', rasterstyle)

    # fetch tiles using the landez TileManager
    tm = create_tiles_manager(parameters)
    zoomlevel = calc_zoomlevel(parameters.pagewidth, parameters.pageheight, parameters.dpi, \
                               parameters.scale_factor, parameters.tile_size, \
                               parameters.minlon, parameters.minlat, \
                               parameters.maxlon, parameters.maxlat)
    if parameters.verbose:
        print("Calculated zoomlevel = %d" % zoomlevel[0])

    for tile in tm.tileslist(bbox = (parameters.minlon, parameters.minlat, \
                                     parameters.maxlon, parameters.maxlat), \
                             zoomlevels = zoomlevel):
        # calc tile metadata
        tile_path = tm.cache.tile_fullpath(tile)
        proj = GoogleProjection(tm.tile_size, zoomlevel, tm.tile_scheme)
        (tile_lox, tile_loy, tile_hix, tile_hiy) = proj.tile_bbox(tile)
        try:
            # make sure the tile is on disk; tiledata is not needed
            tiledata = tm.tile(tile)
            # add to mapnik layer
            rasterlayer = mapnik.Layer("RasterLayer-%d-%d-%d" % tile)
            rasterlayer.datasource = mapnik.Raster(file = tile_path, \
                                                   lox = tile_lox, loy = tile_loy, \
                                                   hix = tile_hix, hiy = tile_hiy)
            rasterlayer.styles.append('RasterStyle')
            m.layers.append(rasterlayer)
        except ExtractionError:
            print("warning: missing tile zoom=%d x=%d y=%d" % tile)

    for gpxfile in parameters.gpxfiles:
        gpxlayer = mapnik.Layer('GPXLayer')
        gpxlayer.datasource = mapnik.Ogr(file = gpxfile, layer = 'tracks')
        gpxlayer.styles.append('GPXStyle')
        m.layers.append(gpxlayer)

    if parameters.temptrackfile:
        overviewlayer = mapnik.Layer('OverviewLayer')
        overviewlayer.datasource = mapnik.Ogr(file = parameters.temptrackfile, layer = 'tracks')
        overviewlayer.styles.append('GPXStyle')
        m.layers.append(overviewlayer)
    
    if parameters.tempwaypointfile:
        waypointlayer = mapnik.Layer('WaypointLayer')
        waypointlayer.datasource = mapnik.Ogr(file = parameters.tempwaypointfile, layer = 'waypoints')
        waypointlayer.styles.append('WaypointStyle')
        m.layers.append(waypointlayer)

    mapnik.render_to_file(m, parameters.basefilename + "." + parameters.output_format,
                          parameters.output_format,
                          parameters.scale_factor)


def main():
    parameters = parse_commandline()
    assure_bbox_mode(parameters)
    
    render(parameters)


if __name__ == '__main__':
    main()

