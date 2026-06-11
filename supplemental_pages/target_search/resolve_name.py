#!/usr/bin/env python

import sys
import urllib
from xml.dom import minidom

targ_str = sys.argv[1]

targ_url = ('http://vizier.cfa.harvard.edu/viz-bin/nph-sesame/-oxp/SNV?%s' 
       % urllib.quote(targ_str))
targ_xml = urllib.urlopen(targ_url).read()

sesame = minidom.parseString(targ_xml)
ras = sesame.getElementsByTagName('jradeg')
decs = sesame.getElementsByTagName('jdedeg')
if len(ras) and len(decs):
    for ra_node, dec_node in zip(ras, decs):
        print ra_node.childNodes[0].nodeValue, dec_node.childNodes[0].nodeValue
