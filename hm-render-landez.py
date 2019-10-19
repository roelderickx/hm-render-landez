#!/usr/bin/env python

# render_tiles -- render maps on paper using Landez and Mapnik, for use with hikingmap
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

import sys, getopt, math, mapnik
from xml.dom import minidom
from landez import TilesManager, GoogleProjection, ExtractionError

# global constants
inch = 2.54 # cm

class Parameters:
    def __init__(self):
        # default parameters
        self.minlon = 0.0
        self.maxlon = 0.0
        self.minlat = 0.0
        self.maxlat = 0.0
        self.pagewidth = 20.0
        self.pageheight = 28.7
        self.dpi = 300
        self.basefilename = ""
        self.temptrackfile = ""
        self.tempwaypointfile = ""
        self.verbose = False
        self.mbtiles_file = ""
        self.wmts_url = ""
        self.wmts_subdomains = ""
        self.mapnik_stylefile = ""
        self.cache_dir = ""
        self.tile_size = ""
        self.tile_format = ""
        self.tile_scheme = ""
        self.hikingmapstyle = "hikingmap_style.xml"
        self.output_format = "png"
        self.scale_factor = 1.0
        self.gpxfiles = [ ]


    def __usage(self):
        print("Usage: " + sys.argv[0] + " [OPTION]... gpxfiles\n"
              "Render map page using mapnik with an mbtiles datasource\n\n"
              "  -o             Minimum longitude\n"
              "  -O             Maximum longitude\n"
              "  -a             Minimum latitude\n"
              "  -A             Maximum latitude\n"
              "  -w             Page width in cm\n"
              "  -h             Page height in cm\n"
              "  -b             Filename, base without extension\n"
              "  -t             Temp track file to render\n"
              "  -y             Temp waypoints file to render\n"
              "  -v, --verbose  Verbose\n"
              "  --help         Display help and exit\n")


    # returns True if parameters could be parsed successfully
    def parse_commandline(self):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "o:O:a:A:w:h:d:b:t:y:v", [
                "verbose",
                "help"])
        except getopt.GetoptError:
            self.__usage()
            return False
        for opt, arg in opts:
            if opt == "--help":
                self.__usage()
                return False
            elif opt in ("-o"):
                self.minlon = float(arg)
            elif opt in ("-O"):
                self.maxlon = float(arg)
            elif opt in ("-a"):
                self.minlat = float(arg)
            elif opt in ("-A"):
                self.maxlat = float(arg)
            elif opt in ("-w"):
                self.pagewidth = float(arg)
            elif opt in ("-h"):
                self.pageheight = float(arg)
            elif opt in ("-b"):
                self.basefilename = arg
            elif opt in ("-t"):
                self.temptrackfile = arg
            elif opt in ("-y"):
                self.tempwaypointfile = arg
            elif opt in ("-v", "--verbose"):
                self.verbose = True
        
        self.gpxfiles = args

        if self.verbose:
            print("Parameters:")
            print("minlon = " + str(self.minlon))
            print("maxlon = " + str(self.maxlon))
            print("minlat = " + str(self.minlat))
            print("maxlat = " + str(self.maxlat))
            print("pagewidth = " + str(self.pagewidth))
            print("pageheight = " + str(self.pageheight))
            print("dpi = " + str(self.dpi))
            print("basefilename = " + self.basefilename)
            print("temptrackfile = " + self.temptrackfile)
            print("tempwaypointfile = " + self.tempwaypointfile)
            print("gpxfiles = " + ', '.join(self.gpxfiles))

        return True


    def __get_xml_subtag_value(self, xmlnode, sublabelname, defaultvalue):
        elements = xmlnode.getElementsByTagName(sublabelname)
        return str(elements[0].firstChild.nodeValue) \
                      if elements and elements[0].childNodes \
                      else defaultvalue


    def parse_configfile(self):
        xmldoc = minidom.parse("render_tiles.config.xml")
        xmlmapnik = xmldoc.getElementsByTagName('render_tiles')[0]
        
        xmltilesmanager = xmlmapnik.getElementsByTagName('tilesmanager')[0]
        self.mbtiles_file = self.__get_xml_subtag_value(xmltilesmanager, 'mbtiles_file', '')
        self.wmts_url = self.__get_xml_subtag_value(xmltilesmanager, 'wmts_url', '')
        self.wmts_subdomains = self.__get_xml_subtag_value(xmltilesmanager, 'wmts_subdomains', '')
        self.mapnik_stylefile = self.__get_xml_subtag_value(xmltilesmanager, 'mapnik_stylefile', '')
        self.cache_dir = self.__get_xml_subtag_value(xmltilesmanager, 'cache_dir', '')
        self.tile_size = int(self.__get_xml_subtag_value(xmltilesmanager, 'tile_size', ''))
        self.tile_format = self.__get_xml_subtag_value(xmltilesmanager, 'tile_format', '')
        self.tile_scheme = self.__get_xml_subtag_value(xmltilesmanager, 'tile_scheme', '')

        self.hikingmapstyle = self.__get_xml_subtag_value(xmlmapnik, 'hikingmapstyle', \
                                                          'hikingmap_style.xml')
        self.output_format = self.__get_xml_subtag_value(xmlmapnik, 'outputformat', 'pdf')
        self.dpi = int(self.__get_xml_subtag_value(xmlmapnik, 'dpi', '300'))
        self.scale_factor = float(self.__get_xml_subtag_value(xmlmapnik, 'scalefactor', '1.0'))
        
        xmlfontdirlist = xmlmapnik.getElementsByTagName('fontdirs')
        
        for xmlfontdir in xmlfontdirlist:
            fontdir = self.__get_xml_subtag_value(xmlfontdir, 'fontdir', '')
            if fontdir != '':
                mapnik.FontEngine.register_fonts(fontdir, True)
        
        return True
    
    
    def create_tiles_manager(self):
        tm_args = { }
        tm_args['cache'] = True
        if self.mbtiles_file:
            tm_args['mbtiles_file'] = self.mbtiles_file
        if self.wmts_url:
            tm_args['tiles_url'] = self.wmts_url
            tm_args['tiles_headers'] = { }
            tm_args['tiles_headers']['User-Agent'] = 'hikingmap/render_tiles'
            tm_args['tiles_headers']['Accept'] = 'image/png,image/*;q=0.9,*/*;q=0.8'
        if self.wmts_subdomains:
            tm_args['tiles_subdomains'] = self.wmts_subdomains
        if self.mapnik_stylefile:
            tm_args['stylefile'] = self.mapnik_stylefile
        if self.cache_dir:
            tm_args['tiles_dir'] = self.cache_dir
        if self.tile_size:
            tm_args['tile_size'] = self.tile_size
        if self.tile_format:
            tm_args['tile_format'] = self.tile_format
        if self.tile_scheme:
            tm_args['tile_scheme'] = self.tile_scheme
        
        tm = TilesManager(**tm_args)
        
        return tm



# helper functions
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



# MAIN

if not hasattr(mapnik, 'mapnik_version') or mapnik.mapnik_version() < 700:
    raise SystemExit('This script requires Mapnik >= 0.7.0)')

parameters = Parameters()
if not parameters.parse_commandline():
    sys.exit()

if not parameters.parse_configfile():
    sys.exit()

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
tm = parameters.create_tiles_manager()
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

if parameters.temptrackfile != "":
    overviewlayer = mapnik.Layer('OverviewLayer')
    overviewlayer.datasource = mapnik.Ogr(file = parameters.temptrackfile, layer = 'tracks')
    overviewlayer.styles.append('GPXStyle')
    m.layers.append(overviewlayer)
elif parameters.tempwaypointfile != "":
    waypointlayer = mapnik.Layer('WaypointLayer')
    waypointlayer.datasource = mapnik.Ogr(file = parameters.tempwaypointfile, layer = 'waypoints')
    waypointlayer.styles.append('WaypointStyle')
    m.layers.append(waypointlayer)

mapnik.render_to_file(m, parameters.basefilename + "." + parameters.output_format,
                      parameters.output_format,
                      parameters.scale_factor)

