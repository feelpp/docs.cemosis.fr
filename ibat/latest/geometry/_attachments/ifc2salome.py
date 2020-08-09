# -*- coding: utf-8 -*-

import sys
import salome


salome.salome_init()
theStudy = salome.myStudy

import GEOM
from salome.geom import geomBuilder
import math
import SALOMEDS


geompy = geomBuilder.New(theStudy)

# import brep and explode it
# tag::import[]
AFC_brep_1 = geompy.ImportBREP("/media/sf_SharedFolder/AFC.brep" )
# end::import[]
# tag::extract_brep[]
listSolid1 = geompy.ExtractShapes(AFC_brep_1, geompy.ShapeType["SOLID"], True)
Partition_1 = geompy.MakePartition(listSolid1, [], [], [], geompy.ShapeType["SOLID"], 0, [], 0)
# end::extract_brep[]

# compute center of mass for each solid
# tag::center_of_mass[]
cmSolid = []
for s in listSolid1:
    cm = geompy.MakeCDG(s)
    cmSolid.append(geompy.PointCoordinates(cm))
# end::center_of_mass[]

# create partition with all solids and create the solids for the air
# tag::create_air[]
Bounding_Box_1 = geompy.MakeBoundingBox(Partition_1, True)
[Shell_1] = geompy.ExtractShapes(Bounding_Box_1, geompy.ShapeType["SHELL"], True)
Solid_69 = geompy.MakeSolid([Shell_1])
Cut_1 = geompy.MakeCutList(Solid_69, [Partition_1], True)
listAir = geompy.SubShapeAllSortedCentres(Cut_1, geompy.ShapeType["SOLID"])
# end::create_air[]

# check if the air is in the building
# tag::check_air[]
listAir1 = []
i = 0
dArray = [1,-1] # before or after direction
xyzArray = [0,1,2] # direction x y and z
for a in listAir:
    cm = geompy.MakeCDG(a)
    cmcoords = geompy.PointCoordinates(cm) 
    isInAll = True
    for xyz in xyzArray:
        for d in dArray:
            isIn = False
            for c in cmSolid:
                isIn = isIn or d*cmcoords[xyz] < d*c[xyz]
            isInAll = isInAll and isIn
    if isInAll:
        listAir1.append(a)
        geompy.addToStudyInFather( Cut_1, a, 'Air_'+str(i))
        i += 1
# end::check_air[]

# make partition with all solids from brep + the air
# tag::make_partition[]
Partition_2 = geompy.MakePartition([Partition_1] + listAir1, [], [], [], geompy.ShapeType["SOLID"], 0, [], 0)
listSolid2 = geompy.ExtractShapes(Partition_2, geompy.ShapeType["SOLID"], True)
# end::make_partition[]

# tag::add_to_study[]
geompy.addToStudy( Partition_2, 'Partition_2' )
for i in range(0,len(listSolid2)):
    geompy.addToStudyInFather( Partition_2, listSolid2[i], 'Solid_'+str(i))
# end::add_to_study[]
