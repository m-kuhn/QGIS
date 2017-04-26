# -*- coding: utf-8 -*-

"""
***************************************************************************
    ScriptUtils.py
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
from builtins import object

__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
from qgis.core import (QgsProcessingUtils,
                       QgsMessageLog)
from processing.core.ProcessingConfig import ProcessingConfig
from processing.script.ScriptAlgorithm import ScriptAlgorithm
from processing.script.WrongScriptException import WrongScriptException
from processing.tools.system import mkdir, userFolder

from qgis.PyQt.QtCore import QCoreApplication


class ScriptUtils(object):

    SCRIPTS_FOLDER = 'SCRIPTS_FOLDER'

    @staticmethod
    def defaultScriptsFolder():
        folder = str(os.path.join(userFolder(), 'scripts'))
        mkdir(folder)
        return os.path.abspath(folder)

    @staticmethod
    def scriptsFolders():
        folder = ProcessingConfig.getSetting(ScriptUtils.SCRIPTS_FOLDER)
        if folder is not None:
            return folder.split(';')
        else:
            return [ScriptUtils.defaultScriptsFolder()]

    @staticmethod
    def loadFromFolder(folder):
        if not os.path.exists(folder):
            return []
        algs = []
        for path, subdirs, files in os.walk(folder):
            for descriptionFile in files:
                if descriptionFile.endswith('py'):
                    try:
                        fullpath = os.path.join(path, descriptionFile)
                        alg = ScriptAlgorithm(fullpath)
                        if alg.name().strip() != '':
                            algs.append(alg)
                    except WrongScriptException as e:
                        QgsMessageLog.logMessage(e.msg, QCoreApplication.translate('Processing', 'Processing'), QgsMessageLog.CRITICAL)
                    except Exception as e:
                        QgsMessageLog.logMessage(
                            QCoreApplication.translate('Processing', 'Could not load script: {0}\n{1}').format(descriptionFile, str(e)),
                            QCoreApplication.translate('Processing', 'Processing'),
                            QgsMessageLog.CRITICAL
                        )
        return algs
