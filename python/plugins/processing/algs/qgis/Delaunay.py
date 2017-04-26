# -*- coding: utf-8 -*-

"""
***************************************************************************
    Delaunay.py
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
from builtins import next

__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant

from qgis.core import QgsField, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsPoint, QgsWkbTypes, QgsProcessingUtils

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

from . import voronoi

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class Delaunay(GeoAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'images', 'ftools', 'delaunay.png'))

    def group(self):
        return self.tr('Vector geometry tools')

    def name(self):
        return 'delaunaytriangulation'

    def displayName(self):
        return self.tr('Delaunay triangulation')

    def defineCharacteristics(self):
        self.addParameter(ParameterVector(self.INPUT,
                                          self.tr('Input layer'), [dataobjects.TYPE_VECTOR_POINT]))

        self.addOutput(OutputVector(self.OUTPUT,
                                    self.tr('Delaunay triangulation'),
                                    datatype=[dataobjects.TYPE_VECTOR_POLYGON]))

    def processAlgorithm(self, context, feedback):
        layer = dataobjects.getLayerFromString(
            self.getParameterValue(self.INPUT))

        fields = [QgsField('POINTA', QVariant.Double, '', 24, 15),
                  QgsField('POINTB', QVariant.Double, '', 24, 15),
                  QgsField('POINTC', QVariant.Double, '', 24, 15)]

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(fields,
                                                                     QgsWkbTypes.Polygon, layer.crs())

        pts = []
        ptDict = {}
        ptNdx = -1
        c = voronoi.Context()
        features = QgsProcessingUtils.getFeatures(layer, context)
        total = 100.0 / QgsProcessingUtils.featureCount(layer, context)
        for current, inFeat in enumerate(features):
            geom = QgsGeometry(inFeat.geometry())
            if geom.isNull():
                continue
            if geom.isMultipart():
                points = geom.asMultiPoint()
            else:
                points = [geom.asPoint()]
            for n, point in enumerate(points):
                x = point.x()
                y = point.y()
                pts.append((x, y))
                ptNdx += 1
                ptDict[ptNdx] = (inFeat.id(), n)
            feedback.setProgress(int(current * total))

        if len(pts) < 3:
            raise GeoAlgorithmExecutionException(
                self.tr('Input file should contain at least 3 points. Choose '
                        'another file and try again.'))

        uniqueSet = set(item for item in pts)
        ids = [pts.index(item) for item in uniqueSet]
        sl = voronoi.SiteList([voronoi.Site(*i) for i in uniqueSet])
        c.triangulate = True
        voronoi.voronoi(sl, c)
        triangles = c.triangles
        feat = QgsFeature()

        total = 100.0 / len(triangles)
        for current, triangle in enumerate(triangles):
            indices = list(triangle)
            indices.append(indices[0])
            polygon = []
            attrs = []
            step = 0
            for index in indices:
                fid, n = ptDict[ids[index]]
                request = QgsFeatureRequest().setFilterFid(fid)
                inFeat = next(layer.getFeatures(request))
                geom = QgsGeometry(inFeat.geometry())
                if geom.isMultipart():
                    point = QgsPoint(geom.asMultiPoint()[n])
                else:
                    point = QgsPoint(geom.asPoint())
                polygon.append(point)
                if step <= 3:
                    attrs.append(ids[index])
                step += 1
            feat.setAttributes(attrs)
            geometry = QgsGeometry().fromPolygon([polygon])
            feat.setGeometry(geometry)
            writer.addFeature(feat)
            feedback.setProgress(int(current * total))

        del writer
