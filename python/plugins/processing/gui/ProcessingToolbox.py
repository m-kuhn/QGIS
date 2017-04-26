# -*- coding: utf-8 -*-

"""
***************************************************************************
    ProcessingToolbox.py
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
from builtins import range


__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import QMenu, QAction, QTreeWidgetItem, QLabel, QMessageBox
from qgis.utils import iface
from qgis.core import (QgsApplication,
                       QgsProcessingAlgorithm)

from processing.gui.Postprocessing import handleAlgorithmResults
from processing.core.Processing import Processing
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig, settingsWatcher
from processing.gui.MessageDialog import MessageDialog
from processing.gui.AlgorithmDialog import AlgorithmDialog
from processing.gui.BatchAlgorithmDialog import BatchAlgorithmDialog
from processing.gui.EditRenderingStylesDialog import EditRenderingStylesDialog
from processing.gui.ConfigDialog import ConfigDialog
from processing.gui.MessageBarProgress import MessageBarProgress
from processing.gui.AlgorithmExecutor import execute
from processing.gui.ProviderActions import (ProviderActions,
                                            ProviderContextMenuActions)

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'ProcessingToolbox.ui'))


class ProcessingToolbox(BASE, WIDGET):

    def __init__(self):
        super(ProcessingToolbox, self).__init__(None)
        self.tipWasClosed = False
        self.setupUi(self)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.searchBox.textChanged.connect(self.textChanged)
        self.algorithmTree.customContextMenuRequested.connect(
            self.showPopupMenu)
        self.algorithmTree.doubleClicked.connect(self.executeAlgorithm)
        self.txtDisabled.setVisible(False)
        self.txtTip.setVisible(self.disabledProviders())
        self.txtDisabled.linkActivated.connect(self.showDisabled)

        def openSettings(url):
            if url == "close":
                self.txtTip.setVisible(False)
                self.tipWasClosed = True
            else:
                iface.showOptionsDialog(iface.mainWindow(), 'processingOptions')
                self.txtTip.setVisible(self.disabledProviders())
        self.txtTip.linkActivated.connect(openSettings)
        if hasattr(self.searchBox, 'setPlaceholderText'):
            self.searchBox.setPlaceholderText(self.tr('Search...'))

        self.fillTree()

        QgsApplication.processingRegistry().providerRemoved.connect(self.removeProvider)
        QgsApplication.processingRegistry().providerAdded.connect(self.addProvider)
        settingsWatcher.settingsChanged.connect(self.fillTree)

    def showDisabled(self):
        self.txtDisabled.setVisible(False)
        for provider_id in self.disabledWithMatchingAlgs:
            self.disabledProviderItems[provider_id].setHidden(False)
        self.algorithmTree.expandAll()

    def disabledProviders(self):
        showTip = ProcessingConfig.getSetting(ProcessingConfig.SHOW_PROVIDERS_TOOLTIP)
        if not showTip or self.tipWasClosed:
            return False

        for provider in QgsApplication.processingRegistry().providers():
            if not provider.isActive():
                return True

        return False

    def textChanged(self):
        text = self.searchBox.text().strip(' ').lower()
        for item in list(self.disabledProviderItems.values()):
            item.setHidden(True)
        self._filterItem(self.algorithmTree.invisibleRootItem(), [t for t in text.split(' ') if t])
        if text:
            self.algorithmTree.expandAll()
            self.disabledWithMatchingAlgs = []
            for provider in QgsApplication.processingRegistry().providers():
                if not provider.isActive():
                    for alg in provider.algorithms():
                        if text in alg.name():
                            self.disabledWithMatchingAlgs.append(provider.id())
                            break
            showTip = ProcessingConfig.getSetting(ProcessingConfig.SHOW_PROVIDERS_TOOLTIP)
            if showTip:
                self.txtDisabled.setVisible(bool(self.disabledWithMatchingAlgs))
        else:
            self.algorithmTree.collapseAll()
            self.algorithmTree.invisibleRootItem().child(0).setExpanded(True)
            self.txtDisabled.setVisible(False)

    def _filterItem(self, item, text):
        if (item.childCount() > 0):
            show = False
            for i in range(item.childCount()):
                child = item.child(i)
                showChild = self._filterItem(child, text)
                show = (showChild or show) and item not in list(self.disabledProviderItems.values())
            item.setHidden(not show)
            return show
        elif isinstance(item, (TreeAlgorithmItem, TreeActionItem)):
            # hide if every part of text is not contained somewhere in either the item text or item user role
            item_text = [item.text(0).lower(), item.data(0, Qt.UserRole).lower()]
            if isinstance(item, TreeAlgorithmItem):
                item_text.append(item.alg.id())
                item_text.extend(item.data(0, Qt.UserRole + 1))

            hide = bool(text) and not all(
                any(part in t for t in item_text)
                for part in text)

            item.setHidden(hide)
            return not hide
        else:
            item.setHidden(True)
            return False

    def activateProvider(self, id):
        provider = QgsApplication.processingRegistry().providerById(id)
        if not provider.canBeActivated():
            QMessageBox.warning(self, self.tr("Activate provider"),
                                self.tr("The provider has been activated, but it might need additional configuration."))
            return

        try:
            # not part of the base class - only some providers have a setActive member
            provider.setActive(True)
            self.fillTree()
            self.textChanged()
            self.showDisabled()
        except:
            QMessageBox.warning(self, self.tr("Activate provider"),
                                self.tr("The provider could not be activated."))

    def updateProvider(self):
        provider = self.sender()
        item = self._providerItem(provider.id())
        if item is not None:
            item.refresh()
            item.sortChildren(0, Qt.AscendingOrder)
            for i in range(item.childCount()):
                item.child(i).sortChildren(0, Qt.AscendingOrder)
            self.addRecentAlgorithms(True)

    def removeProvider(self, provider_id):
        item = self._providerItem(provider_id)
        if item is not None:
            self.algorithmTree.invisibleRootItem().removeChild(item)

    def _providerItem(self, provider_id):
        for i in range(self.algorithmTree.invisibleRootItem().childCount()):
            child = self.algorithmTree.invisibleRootItem().child(i)
            if isinstance(child, TreeProviderItem):
                if child.provider.id() == provider_id:
                    return child

    def showPopupMenu(self, point):
        item = self.algorithmTree.itemAt(point)
        popupmenu = QMenu()
        if isinstance(item, TreeAlgorithmItem):
            alg = item.alg
            executeAction = QAction(self.tr('Execute'), self.algorithmTree)
            executeAction.triggered.connect(self.executeAlgorithm)
            popupmenu.addAction(executeAction)
            if alg.flags() & QgsProcessingAlgorithm.FlagSupportsBatch:
                executeBatchAction = QAction(
                    self.tr('Execute as batch process'),
                    self.algorithmTree)
                executeBatchAction.triggered.connect(
                    self.executeAlgorithmAsBatchProcess)
                popupmenu.addAction(executeBatchAction)
            popupmenu.addSeparator()
            editRenderingStylesAction = QAction(
                self.tr('Edit rendering styles for outputs'),
                self.algorithmTree)
            editRenderingStylesAction.triggered.connect(
                self.editRenderingStyles)
            popupmenu.addAction(editRenderingStylesAction)

        if isinstance(item, (TreeAlgorithmItem, TreeActionItem)):
            data = item.alg if isinstance(item, TreeAlgorithmItem) else item.action
            actions = ProviderContextMenuActions.actions
            if len(actions) > 0:
                popupmenu.addSeparator()
            for action in actions:
                action.setData(data, self)
                if action.isEnabled():
                    contextMenuAction = QAction(action.name,
                                                self.algorithmTree)
                    contextMenuAction.triggered.connect(action.execute)
                    popupmenu.addAction(contextMenuAction)

            popupmenu.exec_(self.algorithmTree.mapToGlobal(point))

    def editRenderingStyles(self):
        item = self.algorithmTree.currentItem()
        if isinstance(item, TreeAlgorithmItem):
            alg = QgsApplication.processingRegistry().algorithmById(item.alg.id())
            dlg = EditRenderingStylesDialog(alg)
            dlg.exec_()

    def executeAlgorithmAsBatchProcess(self):
        item = self.algorithmTree.currentItem()
        if isinstance(item, TreeAlgorithmItem):
            alg = QgsApplication.processingRegistry().algorithmById(item.alg.id())
            alg = alg.getCopy()
            dlg = BatchAlgorithmDialog(alg)
            dlg.show()
            dlg.exec_()

    def executeAlgorithm(self):
        item = self.algorithmTree.currentItem()
        if isinstance(item, TreeAlgorithmItem):
            alg = QgsApplication.processingRegistry().algorithmById(item.alg.id())
            message = alg.checkBeforeOpeningParametersDialog()
            if message:
                dlg = MessageDialog()
                dlg.setTitle(self.tr('Error executing algorithm'))
                dlg.setMessage(
                    self.tr('<h3>This algorithm cannot '
                            'be run :-( </h3>\n{0}').format(message))
                dlg.exec_()
                return
            alg = alg.getCopy()
            if (alg.getVisibleParametersCount() + alg.getVisibleOutputsCount()) > 0:
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
                if dlg.executed:
                    showRecent = ProcessingConfig.getSetting(
                        ProcessingConfig.SHOW_RECENT_ALGORITHMS)
                    if showRecent:
                        self.addRecentAlgorithms(True)
            else:
                feedback = MessageBarProgress()
                execute(alg, None, feedback)
                handleAlgorithmResults(alg, feedback)
                feedback.close()
        if isinstance(item, TreeActionItem):
            action = item.action
            action.setData(self)
            action.execute()

    def fillTree(self):
        self.fillTreeUsingProviders()
        self.addRecentAlgorithms(False)

    def addRecentAlgorithms(self, updating):
        showRecent = ProcessingConfig.getSetting(
            ProcessingConfig.SHOW_RECENT_ALGORITHMS)
        if showRecent:
            recent = ProcessingLog.getRecentAlgorithms()
            if len(recent) != 0:
                found = False
                if updating:
                    recentItem = self.algorithmTree.topLevelItem(0)
                    if recentItem.text(0) == self.tr('Recently used algorithms'):
                        treeWidget = recentItem.treeWidget()
                        treeWidget.takeTopLevelItem(
                            treeWidget.indexOfTopLevelItem(recentItem))

                recentItem = QTreeWidgetItem()
                recentItem.setText(0, self.tr('Recently used algorithms'))
                for algname in recent:
                    alg = QgsApplication.processingRegistry().algorithmById(algname)
                    if alg is not None:
                        algItem = TreeAlgorithmItem(alg)
                        recentItem.addChild(algItem)
                        found = True
                if found:
                    self.algorithmTree.insertTopLevelItem(0, recentItem)
                    recentItem.setExpanded(True)

            self.algorithmTree.setWordWrap(True)

    def addProvider(self, provider_id):
        provider = QgsApplication.processingRegistry().providerById(provider_id)
        providerItem = TreeProviderItem(provider, self.algorithmTree, self)
        if not provider.isActive():
            providerItem.setHidden(True)
            self.disabledProviderItems[provider.id()] = providerItem

        for i in range(self.algorithmTree.invisibleRootItem().childCount()):
            child = self.algorithmTree.invisibleRootItem().child(i)
            if isinstance(child, TreeProviderItem):
                if child.text(0) > providerItem.text(0):
                    break
        self.algorithmTree.insertTopLevelItem(i, providerItem)
        provider.algorithmsLoaded.connect(self.updateProvider)

    def fillTreeUsingProviders(self):
        self.algorithmTree.clear()
        self.disabledProviderItems = {}
        disabled = []
        for provider in QgsApplication.processingRegistry().providers():
            if provider.isActive():
                providerItem = TreeProviderItem(provider, self.algorithmTree, self)
            else:
                disabled.append(provider)
        self.algorithmTree.sortItems(0, Qt.AscendingOrder)
        for provider in disabled:
            providerItem = TreeProviderItem(provider, self.algorithmTree, self)
            providerItem.setHidden(True)
            self.disabledProviderItems[provider.id()] = providerItem


class TreeAlgorithmItem(QTreeWidgetItem):

    def __init__(self, alg):
        QTreeWidgetItem.__init__(self)
        self.alg = alg
        icon = alg.icon()
        nameEn = alg.name()
        name = alg.displayName()
        name = name if name != '' else nameEn
        self.setIcon(0, icon)
        self.setToolTip(0, name)
        self.setText(0, name)
        self.setData(0, Qt.UserRole, nameEn)
        self.setData(0, Qt.UserRole + 1, alg.tags())


class TreeActionItem(QTreeWidgetItem):

    def __init__(self, action):
        QTreeWidgetItem.__init__(self)
        self.action = action
        self.setText(0, action.i18n_name)
        self.setIcon(0, action.getIcon())
        self.setData(0, Qt.UserRole, action.name)


class TreeProviderItem(QTreeWidgetItem):

    def __init__(self, provider, tree, toolbox):
        QTreeWidgetItem.__init__(self, tree)
        self.tree = tree
        self.toolbox = toolbox
        self.provider = provider
        self.setIcon(0, self.provider.icon())
        self.populate()

    def refresh(self):
        self.takeChildren()
        self.populate()

    def populate(self):
        groups = {}
        count = 0
        algs = self.provider.algorithms()
        active = self.provider.isActive()

        # Add algorithms
        for alg in algs:
            if alg.flags() & QgsProcessingAlgorithm.FlagHideFromToolbox:
                continue
            if alg.group() in groups:
                groupItem = groups[alg.group()]
            else:
                groupItem = QTreeWidgetItem()
                name = alg.group()
                if not active:
                    groupItem.setForeground(0, Qt.darkGray)
                groupItem.setText(0, name)
                groupItem.setToolTip(0, name)
                groups[alg.group()] = groupItem
            algItem = TreeAlgorithmItem(alg)
            if not active:
                algItem.setForeground(0, Qt.darkGray)
            groupItem.addChild(algItem)
            count += 1

        if self.provider.id() in ProviderActions.actions:
            actions = ProviderActions.actions[self.provider.id()]
            for action in actions:
                if action.group in groups:
                    groupItem = groups[action.group]
                else:
                    groupItem = QTreeWidgetItem()
                    groupItem.setText(0, action.group)
                    groups[action.group] = groupItem
                algItem = TreeActionItem(action)
                groupItem.addChild(algItem)

        text = self.provider.name()

        if not active:
            def activateProvider():
                self.toolbox.activateProvider(self.provider.id())
            label = QLabel(text + "&nbsp;&nbsp;&nbsp;&nbsp;<a href='%s'>Activate</a>")
            label.setStyleSheet("QLabel {background-color: white; color: grey;}")
            label.linkActivated.connect(activateProvider)
            self.tree.setItemWidget(self, 0, label)

        else:
            text += QCoreApplication.translate("TreeProviderItem", " [{0} geoalgorithms]").format(count)
        self.setText(0, text)
        self.setToolTip(0, self.text(0))
        for groupItem in list(groups.values()):
            self.addChild(groupItem)

        self.setHidden(self.childCount() == 0)
