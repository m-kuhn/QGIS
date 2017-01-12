# -*- coding: utf-8 -*-

"""
***************************************************************************
    ScriptAlgorithm.py
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
import re
import json
from qgis.core import (QgsExpressionContextUtils,
                       QgsExpressionContext,
                       QgsProject,
                       QgsApplication)

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.gui.Help2Html import getHtmlFromHelpFile
from processing.core.parameters import getParameterFromString
from processing.core.outputs import getOutputFromString
from processing.core.ProcessingLog import ProcessingLog
from processing.script.WrongScriptException import WrongScriptException

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ScriptAlgorithm(GeoAlgorithm):

    def __init__(self, descriptionFile, script=None):
        """The script parameter can be used to directly pass the code
        of the script without a file.

        This is to be used from the script edition dialog, but should
        not be used in other cases.
        """

        GeoAlgorithm.__init__(self)
        self._icon = QgsApplication.getThemeIcon("/processingScript.svg")

        self.script = script
        self.allowEdit = True
        self.noCRSWarning = False
        self.descriptionFile = descriptionFile
        if script is not None:
            self.defineCharacteristicsFromScript()
        if descriptionFile is not None:
            self.defineCharacteristicsFromFile()

    def getCopy(self):
        newone = ScriptAlgorithm(self.descriptionFile)
        newone.provider = self.provider
        return newone

    def icon(self):
        return self._icon

    def defineCharacteristicsFromFile(self):
        self.error = None
        self.script = ''
        filename = os.path.basename(self.descriptionFile)
        self.name = filename[:filename.rfind('.')].replace('_', ' ')
        self.group = self.tr('User scripts', 'ScriptAlgorithm')
        with open(self.descriptionFile) as lines:
            line = lines.readline()
            while line != '':
                if line.startswith('##'):
                    try:
                        self.processParameterLine(line.strip('\n'))
                    except:
                        self.error = self.tr('This script has a syntax errors.\n'
                                             'Problem with line: %s', 'ScriptAlgorithm') % line
                self.script += line
                line = lines.readline()
        if self.group == self.tr('[Test scripts]', 'ScriptAlgorithm'):
            self.showInModeler = False
            self.showInToolbox = False

    def defineCharacteristicsFromScript(self):
        lines = self.script.split('\n')
        self.name, self.i18n_name = self.trAlgorithm('[Unnamed algorithm]', 'ScriptAlgorithm')
        self.group, self.i18n_group = self.trAlgorithm('User scripts', 'ScriptAlgorithm')
        for line in lines:
            if line.startswith('##'):
                try:
                    self.processParameterLine(line.strip('\n'))
                except:
                    pass

    def checkBeforeOpeningParametersDialog(self):
        return self.error

    def checkInputCRS(self):
        if self.noCRSWarning:
            return True
        else:
            return GeoAlgorithm.checkInputCRS(self)

    def createDescriptiveName(self, s):
        return s.replace('_', ' ')

    def processParameterLine(self, line):
        param = None
        line = line.replace('#', '')

        if line == "nomodeler":
            self.showInModeler = False
            return
        if line == "nocrswarning":
            self.noCRSWarning = True
            return
        tokens = line.split('=', 1)
        desc = self.createDescriptiveName(tokens[0])
        if tokens[1].lower().strip() == 'group':
            self.group = self.i18n_group = tokens[0]
            return
        if tokens[1].lower().strip() == 'name':
            self.name = self.i18n_name = tokens[0]
            return

        out = getOutputFromString(line)
        if out is None:
            param = getParameterFromString(line)

        if param is not None:
            self.addParameter(param)
        elif out is not None:
            out.name = tokens[0]
            out.description = desc
            self.addOutput(out)
        else:
            raise WrongScriptException(
                self.tr('Could not load script: %s.\n'
                        'Problem with line "%s"', 'ScriptAlgorithm') % (self.descriptionFile or '', line))

    def processAlgorithm(self, feedback):
        ns = {}
        ns['feedback'] = feedback
        ns['scriptDescriptionFile'] = self.descriptionFile

        for param in self.parameters:
            ns[param.name] = param.value

        for out in self.outputs:
            ns[out.name] = out.value

        variables = re.findall('@[a-zA-Z0-9_]*', self.script)
        script = 'import processing\n'
        script += self.script

        context = QgsExpressionContext()
        context.appendScope(QgsExpressionContextUtils.globalScope())
        context.appendScope(QgsExpressionContextUtils.projectScope(QgsProject.instance()))
        for var in variables:
            varname = var[1:]
            if context.hasVariable(varname):
                script = script.replace(var, context.variable(varname))
            else:
                ProcessingLog.addToLog(ProcessingLog.LOG_WARNING, 'Cannot find variable: %s' % varname)

        exec((script), ns)
        for out in self.outputs:
            out.setValue(ns[out.name])

    def help(self):
        if self.descriptionFile is None:
            return False, None
        helpfile = self.descriptionFile + '.help'
        if os.path.exists(helpfile):
            return True, getHtmlFromHelpFile(self, helpfile)
        else:
            return False, None

    def shortHelp(self):
        if self.descriptionFile is None:
            return None
        helpFile = str(self.descriptionFile) + '.help'
        if os.path.exists(helpFile):
            with open(helpFile) as f:
                try:
                    descriptions = json.load(f)
                    if 'ALG_DESC' in descriptions:
                        return self._formatHelp(str(descriptions['ALG_DESC']))
                except:
                    return None
        return None

    def getParameterDescriptions(self):
        descs = {}
        if self.descriptionFile is None:
            return descs
        helpFile = str(self.descriptionFile) + '.help'
        if os.path.exists(helpFile):
            with open(helpFile) as f:
                try:
                    descriptions = json.load(f)
                    for param in self.parameters:
                        if param.name in descriptions:
                            descs[param.name] = str(descriptions[param.name])
                except:
                    return descs
        return descs
