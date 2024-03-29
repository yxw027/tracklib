# -*- coding: utf-8 -*-
'''
Write GPS track in KML file(s).


'''

import os
import progressbar

import tracklib.core.Utils as utils
import tracklib.core.Operator as Operator

from tracklib.core.Track import Track
from tracklib.core.Network import Network
from tracklib.core.Track import TrackCollection


class KmlWriter:
        
        
    @staticmethod
    def writeToKml(track, path, type="LINE", af=None, c1=[0,0,1,1], c2=[1,0,0,1], name=False):
        '''
        Transforms track/track collection/network into KML string
        path: file to write kml (kml returned in standard output if empty)
        type: "POINT" or "LINE"
        name:   True -> label with point number (in GPS sequence)
                Str  -> label with AF name (no name if AF value is empty or ".")
        af: AF used for coloring in POINT mode
        c1: color for min value (default blue) in POINT mode or color in "LINE" mode
        c2: color for max value (default red) in POINT mode
        '''
		
        # Track collection case
        if isinstance(track, TrackCollection):
            return KmlWriter.__writeCollectionToKml(track, path, c1)

        # Network case
        if isinstance(track, Network):
            return KmlWriter.__writeCollectionToKml(track.getAllEdgeGeoms(), path, c1)
        
        f = open(path, "w")		
		
        clampToGround = True
        for obs in track:
            if obs.position.getZ() != 0:
                clampToGround = False
                break
        
        if not af is None:
            vmin = track.operate(Operator.Operator.MIN, af)
            vmax = track.operate(Operator.Operator.MAX, af)
            
        default_color = c1

        if type not in ["LINE", "POINT"]:
            print("Error in KmlWriter: type '"+type+"' unknown")
            exit()            
        
        if type == "LINE":
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write("<kml xmlns=\"http://earth.google.com/kml/2.1\">\n")
            f.write("  <Document>\n")
            f.write("    <Placemark>\n")
            f.write("      <name>Rover Track</name>\n")
            f.write("      <Style>\n")
            f.write("        <LineStyle>\n")
            f.write("          <color>"+utils.rgbToHex(default_color)[2:]+"</color>\n")
            f.write("        </LineStyle>\n")
            f.write("      </Style>\n")
            f.write("      <LineString>\n")
            f.write("        <coordinates>\n")
            
            for i in range(track.size()):
                f.write("          ")
                f.write('{:15.12f}'.format(track.getObs(i).position.getX()) + ",") 
                f.write('{:15.12f}'.format(track.getObs(i).position.getY()))
                if not clampToGround:
                    f.write("," + '{:15.12f}'.format(track.getObs(i).position.getZ())) 
                f.write("\n")
                
            f.write("        </coordinates>\n")
            f.write("      </LineString>\n")
            f.write("    </Placemark>\n")
            f.write("  </Document>\n")
            f.write("</kml>\n")
            
        if type == "POINT":
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write("<kml xmlns=\"http://earth.google.com/kml/2.1\">\n")
            f.write("  <Document>\n")
        
            for i in range(track.size()):
                f.write("    <Placemark>")
                if name:
                    if isinstance(name, str):
                        naf = str(track.getObsAnalyticalFeature(name, i)).strip()
                        if not (naf in ["", "."]):
                            f.write("      <name>"+naf+"</name>")
                    else:
                        f.write("      <name>"+str(i)+"</name>")
                f.write("      <Style>")
                f.write("        <IconStyle>")
                if not af is None:
                    v = track.getObsAnalyticalFeature(af, i)
                    default_color = utils.interpColors(v, vmin, vmax, c1, c2)
                f.write("          <color>" + utils.rgbToHex(default_color)[2:] + "</color>")
                f.write("          <scale>0.3</scale>")
                f.write("          <Icon><href>http://maps.google.com/mapfiles/kml/pal2/icon18.png</href></Icon>")
                f.write("        </IconStyle>")
                f.write("      </Style>")
                f.write("      <Point>")
                f.write("        <coordinates>")
                f.write("          ")
                f.write('{:15.12f}'.format(track.getObs(i).position.getX()) + ",")
                f.write('{:15.12f}'.format(track.getObs(i).position.getY()) + ",")
                f.write('{:15.12f}'.format(track.getObs(i).position.getZ()))
                f.write("        </coordinates>")
                f.write("      </Point>")
                f.write("    </Placemark>\n")
                
            f.write("  </Document>\n")
            f.write("</kml>\n")
                                    
        f.close()	
        print("KML written in file [" + path + "]") 		
      
      
    def __writeCollectionToKml(tracks, path, c1=[1,1,1,1]):
        
        clampToGround = True
        f = open(path, "w")		

        default_color = c1
        
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        f.write("<kml xmlns=\"http://earth.google.com/kml/2.1\">\n")
        f.write("  <Document>\n")
		
        print("KML writing...")
        for j in progressbar.progressbar(range(tracks.size())):

            track = tracks[j]			

            f.write("    <Placemark>\n")
            f.write("      <name>"+str(track.tid)+"</name>\n")
            f.write("      <Style>\n")
            f.write("        <LineStyle>\n")
            f.write("          <color>"+utils.rgbToHex(default_color)[2:]+"</color>\n")
            f.write("        </LineStyle>\n")
            f.write("      </Style>\n")

            f.write("      <LineString>\n")
            f.write("        <coordinates>\n")
            
            for i in range(track.size()):
                f.write("          ")
                f.write('{:15.12f}'.format(track.getObs(i).position.getX()) + ",")
                f.write('{:15.12f}'.format(track.getObs(i).position.getY()))
                if not clampToGround:
                    f.write("," + '{:15.12f}'.format(track.getObs(i).position.getZ()))
                f.write("\n")
                
            f.write("        </coordinates>\n")
            f.write("      </LineString>\n")

            f.write("    </Placemark>\n")

        f.write("  </Document>\n")
        f.write("</kml>\n")

        f.close()
        print("KML written in file [" + path + "]")      