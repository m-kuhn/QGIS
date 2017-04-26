# -*- coding: utf-8 -*-

"""
***************************************************************************
    CheckValidity.py
    ---------------------
    Date                 : May 2015
    Copyright            : (C) 2015 by Arnaud Morvan
    Email                : arnaud dot morvan at camptocamp dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Arnaud Morvan'
__date__ = 'May 2015'
__copyright__ = '(C) 2015, Arnaud Morvan'

# This will get replaced with a git SHA1 when you do a git archive323

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant

from qgis.core import QgsSettings, QgsGeometry, QgsFeature, QgsField, QgsWkbTypes, QgsProcessingUtils
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector
from processing.core.parameters import ParameterSelection
from processing.core.outputs import OutputVector
from processing.tools import dataobjects, vector

settings_method_key = "/qgis/digitizing/validate_geometries"
pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]


class CheckValidity(GeoAlgorithm):

    INPUT_LAYER = 'INPUT_LAYER'
    METHOD = 'METHOD'
    VALID_OUTPUT = 'VALID_OUTPUT'
    INVALID_OUTPUT = 'INVALID_OUTPUT'
    ERROR_OUTPUT = 'ERROR_OUTPUT'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'images', 'ftools', 'check_geometry.png'))

    def group(self):
        return self.tr('Vector geometry tools')

    def name(self):
        return 'checkvalidity'

    def displayName(self):
        return self.tr('Check validity')

    def defineCharacteristics(self):
        self.methods = [self.tr('The one selected in digitizing settings'),
                        'QGIS',
                        'GEOS']

        self.addParameter(ParameterVector(
            self.INPUT_LAYER,
            self.tr('Input layer')))

        self.addParameter(ParameterSelection(
            self.METHOD,
            self.tr('Method'),
            self.methods))

        self.addOutput(OutputVector(
            self.VALID_OUTPUT,
            self.tr('Valid output')))

        self.addOutput(OutputVector(
            self.INVALID_OUTPUT,
            self.tr('Invalid output')))

        self.addOutput(OutputVector(
            self.ERROR_OUTPUT,
            self.tr('Error output')))

    def processAlgorithm(self, context, feedback):
        settings = QgsSettings()
        initial_method_setting = settings.value(settings_method_key, 1)

        method = self.getParameterValue(self.METHOD)
        if method != 0:
            settings.setValue(settings_method_key, method)
        try:
            self.doCheck(context, feedback)
        finally:
            settings.setValue(settings_method_key, initial_method_setting)

    def doCheck(self, context, feedback):
        layer = dataobjects.getLayerFromString(
            self.getParameterValue(self.INPUT_LAYER))

        settings = QgsSettings()
        method = int(settings.value(settings_method_key, 1))

        valid_output = self.getOutputFromName(self.VALID_OUTPUT)
        valid_fields = layer.fields()
        valid_writer = valid_output.getVectorWriter(
            valid_fields,
            layer.wkbType(),
            layer.crs())
        valid_count = 0

        invalid_output = self.getOutputFromName(self.INVALID_OUTPUT)
        invalid_fields = layer.fields().toList() + [
            QgsField(name='_errors',
                     type=QVariant.String,
                     len=255)]
        invalid_writer = invalid_output.getVectorWriter(
            invalid_fields,
            layer.wkbType(),
            layer.crs())
        invalid_count = 0

        error_output = self.getOutputFromName(self.ERROR_OUTPUT)
        error_fields = [
            QgsField(name='message',
                     type=QVariant.String,
                     len=255)]
        error_writer = error_output.getVectorWriter(
            error_fields,
            QgsWkbTypes.Point,
            layer.crs())
        error_count = 0

        features = QgsProcessingUtils.getFeatures(layer, context)
        total = 100.0 / QgsProcessingUtils.featureCount(layer, context)
        for current, inFeat in enumerate(features):
            geom = inFeat.geometry()
            attrs = inFeat.attributes()

            valid = True
            if not geom.isNull() and not geom.isEmpty():
                errors = list(geom.validateGeometry())
                if errors:
                    # QGIS method return a summary at the end
                    if method == 1:
                        errors.pop()
                    valid = False
                    reasons = []
                    for error in errors:
                        errFeat = QgsFeature()
                        error_geom = QgsGeometry.fromPoint(error.where())
                        errFeat.setGeometry(error_geom)
                        errFeat.setAttributes([error.what()])
                        error_writer.addFeature(errFeat)
                        error_count += 1

                        reasons.append(error.what())

                    reason = "\n".join(reasons)
                    if len(reason) > 255:
                        reason = reason[:252] + '...'
                    attrs.append(reason)

            outFeat = QgsFeature()
            outFeat.setGeometry(geom)
            outFeat.setAttributes(attrs)

            if valid:
                valid_writer.addFeature(outFeat)
                valid_count += 1

            else:
                invalid_writer.addFeature(outFeat)
                invalid_count += 1

            feedback.setProgress(int(current * total))

        del valid_writer
        del invalid_writer
        del error_writer

        if valid_count == 0:
            valid_output.open = False
        if invalid_count == 0:
            invalid_output.open = False
        if error_count == 0:
            error_output.open = False
