# -*- coding: utf-8 -*-

"""
***************************************************************************
    Union.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon

from qgis.core import (QgsFeatureRequest,
                       QgsFeature,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsMessageLog,
                       QgsProcessingUtils)

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]

wkbTypeGroups = {
    'Point': (QgsWkbTypes.Point, QgsWkbTypes.MultiPoint, QgsWkbTypes.Point25D, QgsWkbTypes.MultiPoint25D,),
    'LineString': (QgsWkbTypes.LineString, QgsWkbTypes.MultiLineString, QgsWkbTypes.LineString25D, QgsWkbTypes.MultiLineString25D,),
    'Polygon': (QgsWkbTypes.Polygon, QgsWkbTypes.MultiPolygon, QgsWkbTypes.Polygon25D, QgsWkbTypes.MultiPolygon25D,),
}
for key, value in list(wkbTypeGroups.items()):
    for const in value:
        wkbTypeGroups[const] = key


class Union(GeoAlgorithm):

    INPUT = 'INPUT'
    INPUT2 = 'INPUT2'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'images', 'ftools', 'union.png'))

    def group(self):
        return self.tr('Vector overlay tools')

    def name(self):
        return 'union'

    def displayName(self):
        return self.tr('Union')

    def defineCharacteristics(self):
        self.addParameter(ParameterVector(Union.INPUT,
                                          self.tr('Input layer')))
        self.addParameter(ParameterVector(Union.INPUT2,
                                          self.tr('Input layer 2')))
        self.addOutput(OutputVector(Union.OUTPUT, self.tr('Union')))

    def processAlgorithm(self, context, feedback):
        vlayerA = dataobjects.getLayerFromString(self.getParameterValue(Union.INPUT))
        vlayerB = dataobjects.getLayerFromString(self.getParameterValue(Union.INPUT2))

        geomType = vlayerA.wkbType()
        fields = vector.combineVectorFields(vlayerA, vlayerB)
        writer = self.getOutputFromName(Union.OUTPUT).getVectorWriter(fields,
                                                                      geomType, vlayerA.crs())
        inFeatA = QgsFeature()
        inFeatB = QgsFeature()
        outFeat = QgsFeature()
        indexA = vector.spatialindex(vlayerB)
        indexB = vector.spatialindex(vlayerA)

        count = 0
        nElement = 0
        featuresA = QgsProcessingUtils.getFeatures(vlayerA, context)
        nFeat = QgsProcessingUtils.featureCount(vlayerA, context)
        for inFeatA in featuresA:
            feedback.setProgress(nElement / float(nFeat) * 50)
            nElement += 1
            lstIntersectingB = []
            geom = inFeatA.geometry()
            atMapA = inFeatA.attributes()
            intersects = indexA.intersects(geom.boundingBox())
            if len(intersects) < 1:
                try:
                    outFeat.setGeometry(geom)
                    outFeat.setAttributes(atMapA)
                    writer.addFeature(outFeat)
                except:
                    # This really shouldn't happen, as we haven't
                    # edited the input geom at all
                    QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                             self.tr('Processing'), QgsMessageLog.INFO)
            else:
                request = QgsFeatureRequest().setFilterFids(intersects)

                engine = QgsGeometry.createGeometryEngine(geom.geometry())
                engine.prepareGeometry()

                for inFeatB in vlayerB.getFeatures(request):
                    count += 1

                    atMapB = inFeatB.attributes()
                    tmpGeom = inFeatB.geometry()

                    if engine.intersects(tmpGeom.geometry()):
                        int_geom = geom.intersection(tmpGeom)
                        lstIntersectingB.append(tmpGeom)

                        if not int_geom:
                            # There was a problem creating the intersection
                            QgsMessageLog.logMessage(self.tr('GEOS geoprocessing error: One or more input features have invalid geometry.'),
                                                     self.tr('Processing'), QgsMessageLog.INFO)
                            int_geom = QgsGeometry()
                        else:
                            int_geom = QgsGeometry(int_geom)

                        if int_geom.wkbType() == QgsWkbTypes.Unknown or QgsWkbTypes.flatType(int_geom.geometry().wkbType()) == QgsWkbTypes.GeometryCollection:
                            # Intersection produced different geomety types
                            temp_list = int_geom.asGeometryCollection()
                            for i in temp_list:
                                if i.type() == geom.type():
                                    int_geom = QgsGeometry(i)
                                    try:
                                        outFeat.setGeometry(int_geom)
                                        outFeat.setAttributes(atMapA + atMapB)
                                        writer.addFeature(outFeat)
                                    except:
                                        QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                                                 self.tr('Processing'), QgsMessageLog.INFO)
                        else:
                            # Geometry list: prevents writing error
                            # in geometries of different types
                            # produced by the intersection
                            # fix #3549
                            if int_geom.wkbType() in wkbTypeGroups[wkbTypeGroups[int_geom.wkbType()]]:
                                try:
                                    outFeat.setGeometry(int_geom)
                                    outFeat.setAttributes(atMapA + atMapB)
                                    writer.addFeature(outFeat)
                                except:
                                    QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                                             self.tr('Processing'), QgsMessageLog.INFO)

                # the remaining bit of inFeatA's geometry
                # if there is nothing left, this will just silently fail and we're good
                diff_geom = QgsGeometry(geom)
                if len(lstIntersectingB) != 0:
                    intB = QgsGeometry.unaryUnion(lstIntersectingB)
                    diff_geom = diff_geom.difference(intB)

                if diff_geom.wkbType() == 0 or QgsWkbTypes.flatType(diff_geom.geometry().wkbType()) == QgsWkbTypes.GeometryCollection:
                    temp_list = diff_geom.asGeometryCollection()
                    for i in temp_list:
                        if i.type() == geom.type():
                            diff_geom = QgsGeometry(i)
                try:
                    outFeat.setGeometry(diff_geom)
                    outFeat.setAttributes(atMapA)
                    writer.addFeature(outFeat)
                except:
                    QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                             self.tr('Processing'), QgsMessageLog.INFO)

        length = len(vlayerA.fields())
        atMapA = [None] * length

        featuresA = QgsProcessingUtils.getFeatures(vlayerB, context)
        nFeat = QgsProcessingUtils.featureCount(vlayerB, context)
        for inFeatA in featuresA:
            feedback.setProgress(nElement / float(nFeat) * 100)
            add = False
            geom = inFeatA.geometry()
            diff_geom = QgsGeometry(geom)
            atMap = [None] * length
            atMap.extend(inFeatA.attributes())
            intersects = indexB.intersects(geom.boundingBox())

            if len(intersects) < 1:
                try:
                    outFeat.setGeometry(geom)
                    outFeat.setAttributes(atMap)
                    writer.addFeature(outFeat)
                except:
                    QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                             self.tr('Processing'), QgsMessageLog.INFO)
            else:
                request = QgsFeatureRequest().setFilterFids(intersects)

                # use prepared geometries for faster intersection tests
                engine = QgsGeometry.createGeometryEngine(diff_geom.geometry())
                engine.prepareGeometry()

                for inFeatB in vlayerA.getFeatures(request):
                    atMapB = inFeatB.attributes()
                    tmpGeom = inFeatB.geometry()

                    if engine.intersects(tmpGeom.geometry()):
                        add = True
                        diff_geom = QgsGeometry(diff_geom.difference(tmpGeom))
                    else:
                        try:
                            # Ihis only happens if the bounding box
                            # intersects, but the geometry doesn't
                            outFeat.setGeometry(diff_geom)
                            outFeat.setAttributes(atMap)
                            writer.addFeature(outFeat)
                        except:
                            QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                                     self.tr('Processing'), QgsMessageLog.INFO)

            if add:
                try:
                    outFeat.setGeometry(diff_geom)
                    outFeat.setAttributes(atMap)
                    writer.addFeature(outFeat)
                except:
                    QgsMessageLog.logMessage(self.tr('Feature geometry error: One or more output features ignored due to invalid geometry.'),
                                             self.tr('Processing'), QgsMessageLog.INFO)
            nElement += 1

        del writer
