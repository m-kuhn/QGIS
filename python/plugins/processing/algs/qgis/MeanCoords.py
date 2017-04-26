# -*- coding: utf-8 -*-

"""
***************************************************************************
    MeanCoords.py
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
from builtins import str

__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant

from qgis.core import QgsField, QgsFeature, QgsGeometry, QgsPoint, QgsWkbTypes, QgsProcessingUtils

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import ParameterTableField
from processing.core.parameters import ParameterVector
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class MeanCoords(GeoAlgorithm):

    POINTS = 'POINTS'
    WEIGHT = 'WEIGHT'
    OUTPUT = 'OUTPUT'
    UID = 'UID'
    WEIGHT = 'WEIGHT'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'images', 'ftools', 'mean.png'))

    def group(self):
        return self.tr('Vector analysis tools')

    def name(self):
        return 'meancoordinates'

    def displayName(self):
        return self.tr('Mean coordinate(s)')

    def defineCharacteristics(self):
        self.addParameter(ParameterVector(self.POINTS,
                                          self.tr('Input layer')))
        self.addParameter(ParameterTableField(self.WEIGHT,
                                              self.tr('Weight field'),
                                              MeanCoords.POINTS,
                                              ParameterTableField.DATA_TYPE_NUMBER,
                                              optional=True))
        self.addParameter(ParameterTableField(self.UID,
                                              self.tr('Unique ID field'),
                                              MeanCoords.POINTS,
                                              optional=True))

        self.addOutput(OutputVector(MeanCoords.OUTPUT, self.tr('Mean coordinates'), datatype=[dataobjects.TYPE_VECTOR_POINT]))

    def processAlgorithm(self, context, feedback):
        layer = dataobjects.getLayerFromString(self.getParameterValue(self.POINTS))
        weightField = self.getParameterValue(self.WEIGHT)
        uniqueField = self.getParameterValue(self.UID)

        if weightField is None:
            weightIndex = -1
        else:
            weightIndex = layer.fields().lookupField(weightField)

        if uniqueField is None:
            uniqueIndex = -1
        else:
            uniqueIndex = layer.fields().lookupField(uniqueField)

        fieldList = [QgsField('MEAN_X', QVariant.Double, '', 24, 15),
                     QgsField('MEAN_Y', QVariant.Double, '', 24, 15),
                     QgsField('UID', QVariant.String, '', 255)]

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(
            fieldList, QgsWkbTypes.Point, layer.crs()
        )

        features = QgsProcessingUtils.getFeatures(layer, context)
        total = 100.0 / QgsProcessingUtils.featureCount(layer, context)
        means = {}
        for current, feat in enumerate(features):
            feedback.setProgress(int(current * total))
            if uniqueIndex == -1:
                clazz = "Single class"
            else:
                clazz = str(feat.attributes()[uniqueIndex]).strip()
            if weightIndex == -1:
                weight = 1.00
            else:
                try:
                    weight = float(feat.attributes()[weightIndex])
                except:
                    weight = 1.00

            if weight < 0:
                raise GeoAlgorithmExecutionException(self.tr('Negative weight value found. Please fix your data and try again.'))

            if clazz not in means:
                means[clazz] = (0, 0, 0)

            (cx, cy, totalweight) = means[clazz]
            geom = QgsGeometry(feat.geometry())
            geom = vector.extractPoints(geom)
            for i in geom:
                cx += i.x() * weight
                cy += i.y() * weight
                totalweight += weight
            means[clazz] = (cx, cy, totalweight)

        current = 0
        total = 100.0 / len(means)
        for (clazz, values) in list(means.items()):
            outFeat = QgsFeature()
            cx = values[0] / values[2]
            cy = values[1] / values[2]
            meanPoint = QgsPoint(cx, cy)

            outFeat.setGeometry(QgsGeometry.fromPoint(meanPoint))
            outFeat.setAttributes([cx, cy, clazz])
            writer.addFeature(outFeat)
            current += 1
            feedback.setProgress(int(current * total))

        del writer
