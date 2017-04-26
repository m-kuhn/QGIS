# -*- coding: utf-8 -*-

"""
***************************************************************************
    Processing.py
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
from __future__ import print_function
from builtins import str
from builtins import object

__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import traceback

from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtGui import QCursor

from qgis.utils import iface
from qgis.core import (QgsMessageLog,
                       QgsApplication,
                       QgsProcessingProvider,
                       QgsProcessingUtils)

import processing
from processing.script.ScriptUtils import ScriptUtils
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.gui.MessageBarProgress import MessageBarProgress
from processing.gui.RenderingStyles import RenderingStyles
from processing.gui.Postprocessing import handleAlgorithmResults
from processing.gui.AlgorithmExecutor import execute
from processing.tools import dataobjects

from processing.modeler.ModelerAlgorithmProvider import ModelerAlgorithmProvider  # NOQA
from processing.algs.qgis.QGISAlgorithmProvider import QGISAlgorithmProvider  # NOQA
from processing.algs.grass7.Grass7AlgorithmProvider import Grass7AlgorithmProvider  # NOQA
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider  # NOQA
from processing.algs.r.RAlgorithmProvider import RAlgorithmProvider  # NOQA
from processing.algs.saga.SagaAlgorithmProvider import SagaAlgorithmProvider  # NOQA
from processing.script.ScriptAlgorithmProvider import ScriptAlgorithmProvider  # NOQA
from processing.preconfigured.PreconfiguredAlgorithmProvider import PreconfiguredAlgorithmProvider  # NOQA


class Processing(object):
    BASIC_PROVIDERS = []

    @staticmethod
    def activateProvider(providerOrName, activate=True):
        provider_id = providerOrName.id() if isinstance(providerOrName, QgsProcessingProvider) else providerOrName
        provider = QgsApplication.processingRegistry().providerById(provider_id)
        try:
            provider.setActive(True)
            provider.refreshAlgorithms()
        except:
            # provider could not be activated
            QgsMessageLog.logMessage(Processing.tr('Error: Provider {0} could not be activated\n').format(provider_id),
                                     Processing.tr("Processing"))

    @staticmethod
    def initialize():
        if "model" in [p.id() for p in QgsApplication.processingRegistry().providers()]:
            return
        # Add the basic providers
        for c in QgsProcessingProvider.__subclasses__():
            p = c()
            Processing.BASIC_PROVIDERS.append(p)
            QgsApplication.processingRegistry().addProvider(p)
        # And initialize
        ProcessingConfig.initialize()
        ProcessingConfig.readSettings()
        RenderingStyles.loadStyles()

    @staticmethod
    def deinitialize():
        for p in Processing.BASIC_PROVIDERS:
            QgsApplication.processingRegistry().removeProvider(p)

        Processing.BASIC_PROVIDERS = []

    @staticmethod
    def addScripts(folder):
        Processing.initialize()
        provider = QgsApplication.processingRegistry().providerById("qgis")
        scripts = ScriptUtils.loadFromFolder(folder)
        # fix_print_with_import
        print(scripts)
        for script in scripts:
            script.allowEdit = False
            script._icon = provider._icon
        provider.externalAlgs.extend(scripts)
        provider.refreshAlgorithms()

    @staticmethod
    def removeScripts(folder):
        provider = QgsApplication.processingRegistry().providerById("qgis")
        for alg in provider.externalAlgs[::-1]:
            path = os.path.dirname(alg.descriptionFile)
            if path == folder:
                provider.externalAlgs.remove(alg)
        provider.refreshAlgorithms()

    @staticmethod
    def runAlgorithm(algOrName, onFinish, *args, **kwargs):
        if isinstance(algOrName, GeoAlgorithm):
            alg = algOrName
        else:
            alg = QgsApplication.processingRegistry().algorithmById(algOrName)
        if alg is None:
            # fix_print_with_import
            print('Error: Algorithm not found\n')
            QgsMessageLog.logMessage(Processing.tr('Error: Algorithm {0} not found\n').format(algOrName),
                                     Processing.tr("Processing"))
            return
        alg = alg.getCopy()

        if len(args) == 1 and isinstance(args[0], dict):
            # Set params by name and try to run the alg even if not all parameter values are provided,
            # by using the default values instead.
            setParams = []
            for (name, value) in list(args[0].items()):
                param = alg.getParameterFromName(name)
                if param and param.setValue(value):
                    setParams.append(name)
                    continue
                output = alg.getOutputFromName(name)
                if output and output.setValue(value):
                    continue
                # fix_print_with_import
                print('Error: Wrong parameter value %s for parameter %s.' % (value, name))
                QgsMessageLog.logMessage(
                    Processing.tr('Error: Wrong parameter value {0} for parameter {1}.').format(value, name),
                    Processing.tr("Processing"))
                QgsMessageLog.logMessage(Processing.tr('Error in {0}. Wrong parameter value {1} for parameter {2}.').format(
                    alg.name(), value, name
                ), Processing.tr("Processing"),
                    QgsMessageLog.CRITICAL
                )
                return
            # fill any missing parameters with default values if allowed
            for param in alg.parameters:
                if param.name not in setParams:
                    if not param.setDefaultValue():
                        # fix_print_with_import
                        print('Error: Missing parameter value for parameter %s.' % param.name)
                        QgsMessageLog.logMessage(
                            Processing.tr('Error: Missing parameter value for parameter {0}.').format(param.name),
                            Processing.tr("Processing"))
                        return
        else:
            if len(args) != alg.getVisibleParametersCount() + alg.getVisibleOutputsCount():
                # fix_print_with_import
                print('Error: Wrong number of parameters')
                QgsMessageLog.logMessage(Processing.tr('Error: Wrong number of parameters'),
                                         Processing.tr("Processing"))
                processing.algorithmHelp(algOrName)
                return
            i = 0
            for param in alg.parameters:
                if not param.hidden:
                    if not param.setValue(args[i]):
                        # fix_print_with_import
                        print('Error: Wrong parameter value: ' + str(args[i]))
                        QgsMessageLog.logMessage(Processing.tr('Error: Wrong parameter value: ') + str(args[i]),
                                                 Processing.tr("Processing"))
                        return
                    i = i + 1

            for output in alg.outputs:
                if not output.hidden:
                    if not output.setValue(args[i]):
                        # fix_print_with_import
                        print('Error: Wrong output value: ' + str(args[i]))
                        QgsMessageLog.logMessage(Processing.tr('Error: Wrong output value: ') + str(args[i]),
                                                 Processing.tr("Processing"))
                        return
                    i = i + 1

        msg = alg._checkParameterValuesBeforeExecuting()
        if msg:
            # fix_print_with_import
            print('Unable to execute algorithm\n' + str(msg))
            QgsMessageLog.logMessage(Processing.tr('Unable to execute algorithm\n{0}').format(msg),
                                     Processing.tr("Processing"))
            return

        if not alg.checkInputCRS():
            print('Warning: Not all input layers use the same CRS.\n' +
                  'This can cause unexpected results.')
            QgsMessageLog.logMessage(
                Processing.tr('Warning: Not all input layers use the same CRS.\nThis can cause unexpected results.'),
                Processing.tr("Processing"))

        # Don't set the wait cursor twice, because then when you
        # restore it, it will still be a wait cursor.
        overrideCursor = False
        if iface is not None:
            cursor = QApplication.overrideCursor()
            if cursor is None or cursor == 0:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                overrideCursor = True
            elif cursor.shape() != Qt.WaitCursor:
                QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
                overrideCursor = True

        feedback = None
        if kwargs is not None and "feedback" in list(kwargs.keys()):
            feedback = kwargs["feedback"]
        elif iface is not None:
            feedback = MessageBarProgress(alg.displayName())
        context = dataobjects.createContext()

        ret = execute(alg, context, feedback)
        if ret:
            if onFinish is not None:
                onFinish(alg, feedback)
        else:
            QgsMessageLog.logMessage(Processing.tr("There were errors executing the algorithm."),
                                     Processing.tr("Processing"))

        if overrideCursor:
            QApplication.restoreOverrideCursor()
        if isinstance(feedback, MessageBarProgress):
            feedback.close()
        return alg

    @staticmethod
    def tr(string, context=''):
        if context == '':
            context = 'Processing'
        return QCoreApplication.translate(context, string)
