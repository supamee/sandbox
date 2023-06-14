from pykml.factory import KML_ElementMaker as KML
from lxml import etree
from datetime import datetime, timedelta
import time
from random import random 
name_object = KML.name("Hello World!")
timestamp = datetime.now()
year=2020
month=12
day=10
hour=11
minute=30
second=0
people=("A","B","C")
num_points=3

doc=KML.kml(KML.Document(KML.Name("test")))
timestamp=datetime(year,month,day,hour,minute,second)
for name in people:
    folder=KML.Folder(KML.name(name))
    for i in range(num_points):
        pm1 = KML.Placemark(KML.name(name+str(i)),
                        KML.Point(KML.coordinates(str(-64.0+random())+','+str(18.4607+random()))),
                        KML.TimeStamp(KML.when((timestamp+timedelta(minutes=i)).strftime('%Y-%m-%dT%H:%M:%SZ'))),
                    )
        folder.append(pm1)
    doc.Document.append(folder)

with open("test.kmz","w") as fp:
    fp.write(etree.tostring(doc, pretty_print=True, encoding="unicode"))
print(etree.tostring(doc, pretty_print=True, encoding="unicode"))