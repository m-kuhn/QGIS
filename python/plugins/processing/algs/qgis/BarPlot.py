# -*- coding: utf-8 -*-

"""
***************************************************************************
    BarPlot.py
    ---------------------
    Date                 : January 2013
    Copyright            : (C) 2013 by Victor Olaya
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
__date__ = 'January 2013'
__copyright__ = '(C) 2013, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import plotly as plt
import plotly.graph_objs as go


from qgis.core import (QgsApplication)
from processing.core.parameters import ParameterTable
from processing.core.parameters import ParameterTableField
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.outputs import OutputHTML
from processing.tools import vector
from processing.tools import dataobjects


class BarPlot(GeoAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    NAME_FIELD = 'NAME_FIELD'
    VALUE_FIELD = 'VALUE_FIELD'

    def icon(self):
        return QgsApplication.getThemeIcon("/providerQgis.svg")

    def svgIconPath(self):
        return QgsApplication.iconPath("providerQgis.svg")

    def group(self):
        return self.tr('Graphics')

    def name(self):
        return 'barplot'

    def displayName(self):
        return self.tr('Bar plot')

    def defineCharacteristics(self):
        self.addParameter(ParameterTable(self.INPUT, self.tr('Input table')))
        self.addParameter(ParameterTableField(self.NAME_FIELD,
                                              self.tr('Category name field'),
                                              self.INPUT,
                                              ParameterTableField.DATA_TYPE_ANY))
        self.addParameter(ParameterTableField(self.VALUE_FIELD,
                                              self.tr('Value field'),
                                              self.INPUT,
                                              ParameterTableField.DATA_TYPE_NUMBER))

        self.addOutput(OutputHTML(self.OUTPUT, self.tr('Bar plot')))

    def processAlgorithm(self, context, feedback):
        layer = dataobjects.getLayerFromString(
            self.getParameterValue(self.INPUT))
        namefieldname = self.getParameterValue(self.NAME_FIELD)
        valuefieldname = self.getParameterValue(self.VALUE_FIELD)

        output = self.getOutputValue(self.OUTPUT)

        values = vector.values(layer, context, valuefieldname)

        x_var = [i[namefieldname] for i in layer.getFeatures()]

        data = [go.Bar(x=x_var,
                       y=values[valuefieldname])]
        plt.offline.plot(data, filename=output, auto_open=False)
