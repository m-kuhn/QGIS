# -*- coding: utf-8 -*-

"""
***************************************************************************
    EditScriptDialog.py
    ---------------------
    Date                 : December 2012
    Copyright            : (C) 2012 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'December 2012'
__copyright__ = '(C) 2012, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import codecs
import sys
import json
import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QSize, QByteArray, QSettings
from qgis.PyQt.QtGui import QIcon, QCursor
from qgis.PyQt.QtWidgets import (QMenu,
                                 QAction,
                                 QToolButton,
                                 QMessageBox,
                                 QFileDialog,
                                 QApplication)

from qgis.core import QgsApplication
from qgis.utils import iface

from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.HelpEditionDialog import HelpEditionDialog
from processing.algs.r.RAlgorithm import RAlgorithm
from processing.algs.r.RUtils import RUtils
from processing.script.ScriptAlgorithm import ScriptAlgorithm
from processing.script.ScriptUtils import ScriptUtils

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgScriptEditor.ui'))


class ScriptEditorDialog(BASE, WIDGET):

    SCRIPT_PYTHON = 0
    SCRIPT_R = 1

    hasChanged = False

    def __init__(self, algType, alg):
        super(ScriptEditorDialog, self).__init__(None)
        self.setupUi(self)

        self.setWindowFlags(Qt.WindowMinimizeButtonHint |
                            Qt.WindowMaximizeButtonHint |
                            Qt.WindowCloseButtonHint)

        settings = QSettings()
        self.restoreState(settings.value("/Processing/stateScriptEditor", QByteArray()))
        self.restoreGeometry(settings.value("/Processing/geometryScriptEditor", QByteArray()))

        iconSize = settings.value("iconsize", 24)
        self.toolBar.setIconSize(QSize(iconSize, iconSize))

        self.actionOpenScript.setIcon(
            QgsApplication.getThemeIcon('/mActionFileOpen.svg'))
        self.actionSaveScript.setIcon(
            QgsApplication.getThemeIcon('/mActionFileSave.svg'))
        self.actionSaveScriptAs.setIcon(
            QgsApplication.getThemeIcon('/mActionFileSaveAs.svg'))
        self.actionEditScriptHelp.setIcon(
            QgsApplication.getThemeIcon('/mActionEditHelpContent.svg'))
        self.actionRunScript.setIcon(
            QgsApplication.getThemeIcon('/mActionStart.svg'))
        self.actionCut.setIcon(
            QgsApplication.getThemeIcon('/mActionEditCut.svg'))
        self.actionCopy.setIcon(
            QgsApplication.getThemeIcon('/mActionEditCopy.svg'))
        self.actionPaste.setIcon(
            QgsApplication.getThemeIcon('/mActionEditPaste.svg'))
        self.actionUndo.setIcon(
            QgsApplication.getThemeIcon('/mActionUndo.svg'))
        self.actionRedo.setIcon(
            QgsApplication.getThemeIcon('/mActionRedo.svg'))
        self.actionIncreaseFontSize.setIcon(
            QgsApplication.getThemeIcon('/mActionIncreaseFont.svg'))
        self.actionDecreaseFontSize.setIcon(
            QgsApplication.getThemeIcon('/mActionDecreaseFont.svg'))

        # Connect signals and slots
        self.actionOpenScript.triggered.connect(self.openScript)
        self.actionSaveScript.triggered.connect(self.save)
        self.actionSaveScriptAs.triggered.connect(self.saveAs)
        self.actionEditScriptHelp.triggered.connect(self.editHelp)
        self.actionRunScript.triggered.connect(self.runAlgorithm)
        self.actionCut.triggered.connect(self.editor.cut)
        self.actionCopy.triggered.connect(self.editor.copy)
        self.actionPaste.triggered.connect(self.editor.paste)
        self.actionUndo.triggered.connect(self.editor.undo)
        self.actionRedo.triggered.connect(self.editor.redo)
        self.actionIncreaseFontSize.triggered.connect(self.editor.zoomIn)
        self.actionDecreaseFontSize.triggered.connect(self.editor.zoomOut)
        self.editor.textChanged.connect(lambda: self.setHasChanged(True))

        self.alg = alg
        self.algType = algType

        self.snippets = {}
        if self.algType == self.SCRIPT_PYTHON:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "script", "snippets.py")
            with codecs.open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            snippetlines = []
            name = None
            for line in lines:
                if line.startswith("##"):
                    if snippetlines:
                        self.snippets[name] = "".join(snippetlines)
                    name = line[2:]
                    snippetlines = []
                else:
                    snippetlines.append(line)
            if snippetlines:
                self.snippets[name] = "".join(snippetlines)

        #if self.snippets:
        #    self.btnSnippets.setVisible(False)

        if self.alg is not None:
            self.filename = self.alg.descriptionFile
            self.editor.setText(self.alg.script)
        else:
            self.filename = None

        self.update = False
        self.help = None

        self.setHasChanged(False)

        self.editor.setLexerType(self.algType)

    #def showSnippets(self, evt):
    #    popupmenu = QMenu()
    #    for name, snippet in list(self.snippets.items()):
    #        action = QAction(self.tr(name), self.btnSnippets)
    #        action.triggered[()].connect(lambda snippet=snippet: self.editor.insert(snippet))
    #    popupmenu.addAction(action)
    #    popupmenu.exec_(QCursor.pos())

    def closeEvent(self, evt):
        if self.hasChanged:
            ret = QMessageBox.question(self, self.tr('Unsaved changes'),
                                       self.tr('There are unsaved changes in script. Continue?'),
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                                       )
            if ret == QMessageBox.Yes:
                evt.accept()
            else:
                evt.ignore()
        else:
            evt.accept()

    def editHelp(self):
        if self.alg is None:
            if self.algType == self.SCRIPT_PYTHON:
                alg = ScriptAlgorithm(None, self.editor.text())
            elif self.algType == self.SCRIPT_R:
                alg = RAlgorithm(None, self.editor.text())
        else:
            alg = self.alg

        dlg = HelpEditionDialog(alg)
        dlg.exec_()
        if dlg.descriptions:
            self.help = dlg.descriptions
            self.setHasChanged(True)

    def openScript(self):
        if self.hasChanged:
            ret = QMessageBox.warning(self, self.tr('Unsaved changes'),
                                      self.tr('There are unsaved changes in script. Continue?'),
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ret == QMessageBox.No:
                return

        if self.algType == self.SCRIPT_PYTHON:
            scriptDir = ScriptUtils.scriptsFolders()[0]
            filterName = self.tr('Python scripts (*.py)')
        elif self.algType == self.SCRIPT_R:
            scriptDir = RUtils.RScriptsFolders()[0]
            filterName = self.tr('Processing R script (*.rsx)')

        self.filename, fileFilter = QFileDialog.getOpenFileName(
            self, self.tr('Open script'), scriptDir, filterName)

        if self.filename == '':
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        with codecs.open(self.filename, 'r', encoding='utf-8') as f:
            txt = f.read()

        self.editor.setText(txt)
        self.hasChanged = False
        self.editor.setModified(False)
        self.editor.recolor()
        QApplication.restoreOverrideCursor()

    def save(self):
        self.saveScript(False)

    def saveAs(self):
        self.saveScript(True)

    def saveScript(self, saveAs):
        if self.filename is None or saveAs:
            if self.algType == self.SCRIPT_PYTHON:
                scriptDir = ScriptUtils.scriptsFolders()[0]
                filterName = self.tr('Python scripts (*.py)')
            elif self.algType == self.SCRIPT_R:
                scriptDir = RUtils.RScriptsFolders()[0]
                filterName = self.tr('Processing R script (*.rsx)')

            self.filename, fileFilter = QFileDialog.getSaveFileName(
                self, self.tr('Save script'), scriptDir, filterName)

        if self.filename:
            if self.algType == self.SCRIPT_PYTHON and \
                    not self.filename.lower().endswith('.py'):
                self.filename += '.py'
            if self.algType == self.SCRIPT_R and \
                    not self.filename.lower().endswith('.rsx'):
                self.filename += '.rsx'

            text = self.editor.text()
            if self.alg is not None:
                self.alg.script = text
            try:
                with codecs.open(self.filename, 'w', encoding='utf-8') as fout:
                    fout.write(text)
            except IOError:
                QMessageBox.warning(self,
                                    self.tr('I/O error'),
                                    self.tr('Unable to save edits. Reason:\n{}').format(sys.exc_info()[1])
                                    )
                return
            self.update = True

            # If help strings were defined before saving the script for
            # the first time, we do it here
            if self.help:
                with codecs.open(self.filename + '.help', 'w', encoding='utf-8') as f:
                    json.dump(self.help, f)
                self.help = None
            self.setHasChanged(False)
        else:
            self.filename = None

    def setHasChanged(self, hasChanged):
        self.hasChanged = hasChanged
        self.actionSaveScript.setEnabled(hasChanged)

    def runAlgorithm(self):
        if self.algType == self.SCRIPT_PYTHON:
            alg = ScriptAlgorithm(None, self.editor.text())
            alg.provider = QgsApplication.processingRegistry().providerById('script')
        if self.algType == self.SCRIPT_R:
            alg = RAlgorithm(None, self.editor.text())
            alg.provider = QgsApplication.processingRegistry().providerById('r')

        dlg = alg.getCustomParametersDialog()
        if not dlg:
            dlg = AlgorithmDialog(alg)

        canvas = iface.mapCanvas()
        prevMapTool = canvas.mapTool()

        dlg.show()
        dlg.exec_()

        if canvas.mapTool() != prevMapTool:
            try:
                canvas.mapTool().reset()
            except:
                pass
            canvas.setMapTool(prevMapTool)
