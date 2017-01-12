# -*- coding: utf-8 -*-

"""
***************************************************************************
    ExtractByLocation.py
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

from qgis.core import QgsFeatureRequest
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterSelection
from processing.core.parameters import ParameterNumber
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector


class ExtractByLocation(GeoAlgorithm):

    INPUT = 'INPUT'
    INTERSECT = 'INTERSECT'
    PREDICATE = 'PREDICATE'
    PRECISION = 'PRECISION'
    OUTPUT = 'OUTPUT'

    def defineCharacteristics(self):
        self.name, self.i18n_name = self.trAlgorithm('Extract by location')
        self.group, self.i18n_group = self.trAlgorithm('Vector selection tools')
        self.tags = self.tr('extract,filter,location,intersects,contains,within')

        self.predicates = (
            ('intersects', self.tr('intersects')),
            ('contains', self.tr('contains')),
            ('disjoint', self.tr('disjoint')),
            ('equals', self.tr('equals')),
            ('touches', self.tr('touches')),
            ('overlaps', self.tr('overlaps')),
            ('within', self.tr('within')),
            ('crosses', self.tr('crosses')))

        self.addParameter(ParameterVector(self.INPUT,
                                          self.tr('Layer to select from')))
        self.addParameter(ParameterVector(self.INTERSECT,
                                          self.tr('Additional layer (intersection layer)')))
        self.addParameter(ParameterSelection(self.PREDICATE,
                                             self.tr('Geometric predicate'),
                                             self.predicates,
                                             multiple=True))
        self.addParameter(ParameterNumber(self.PRECISION,
                                          self.tr('Precision'),
                                          0.0, None, 0.0))
        self.addOutput(OutputVector(self.OUTPUT, self.tr('Extracted (location)')))

    def processAlgorithm(self, feedback):
        filename = self.getParameterValue(self.INPUT)
        layer = dataobjects.getObjectFromUri(filename)
        filename = self.getParameterValue(self.INTERSECT)
        selectLayer = dataobjects.getObjectFromUri(filename)
        predicates = self.getParameterValue(self.PREDICATE)
        precision = self.getParameterValue(self.PRECISION)

        index = vector.spatialindex(layer)

        output = self.getOutputFromName(self.OUTPUT)
        writer = output.getVectorWriter(layer.fields(),
                                        layer.wkbType(), layer.crs())

        if 'disjoint' in predicates:
            disjoinSet = []
            for feat in vector.features(layer):
                disjoinSet.append(feat.id())

        selectedSet = []
        features = vector.features(selectLayer)
        total = 100.0 / len(features)
        for current, f in enumerate(features):
            geom = vector.snapToPrecision(f.geometry(), precision)
            bbox = vector.bufferedBoundingBox(geom.boundingBox(), 0.51 * precision)
            intersects = index.intersects(bbox)
            request = QgsFeatureRequest().setFilterFids(intersects).setSubsetOfAttributes([])
            for feat in layer.getFeatures(request):
                tmpGeom = vector.snapToPrecision(feat.geometry(), precision)
                res = False
                for predicate in predicates:
                    if predicate == 'disjoint':
                        if tmpGeom.intersects(geom):
                            try:
                                disjoinSet.remove(feat.id())
                            except:
                                pass  # already removed
                    else:
                        res = getattr(tmpGeom, predicate)(geom)
                        if res:
                            selectedSet.append(feat.id())
                            break

            feedback.setProgress(int(current * total))

        if 'disjoint' in predicates:
            selectedSet = selectedSet + disjoinSet

        features = vector.features(layer)
        total = 100.0 / len(features)
        for current, f in enumerate(features):
            if f.id() in selectedSet:
                writer.addFeature(f)
            feedback.setProgress(int(current * total))
        del writer
