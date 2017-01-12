# -*- coding: utf-8 -*-

"""
***************************************************************************
    ModelerAlgorithm.py
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

import os.path
import sys
import copy
import time
import json
import codecs
import traceback
from qgis.PyQt.QtCore import QCoreApplication, QPointF
from qgis.PyQt.QtGui import QIcon
from operator import attrgetter

from qgis.core import QgsApplication
from qgis.gui import QgsMessageBar
from qgis.utils import iface
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.modeler.WrongModelException import WrongModelException
from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.parameters import (getParameterFromString,
                                        ParameterRaster,
                                        ParameterVector,
                                        ParameterTable,
                                        ParameterTableField,
                                        ParameterBoolean,
                                        ParameterString,
                                        ParameterNumber,
                                        ParameterExtent,
                                        ParameterCrs,
                                        ParameterDataObject,
                                        ParameterMultipleInput)

from processing.gui.Help2Html import getHtmlFromDescriptionsDict
from processing.core.alglist import algList

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class ModelerParameter(object):

    def __init__(self, param=None, pos=None):
        self.param = param
        self.pos = pos

    def todict(self):
        return self.__dict__

    @staticmethod
    def fromdict(d):
        return ModelerParameter(d["param"], d["pos"])


class ModelerOutput(object):

    def __init__(self, description=""):
        self.description = description
        self.pos = None

    def todict(self):
        return self.__dict__


class Algorithm(object):

    def __init__(self, consoleName=""):

        self.name = None
        self.description = ""

        # The type of the algorithm, indicated as a string, which corresponds
        # to the string used to refer to it in the python console
        self.consoleName = consoleName

        self._algInstance = None

        # A dict of Input object. keys are param names
        self.params = {}

        # A dict of ModelerOutput with final output descriptions. Keys are output names.
        # Outputs not final are not stored in this dict
        self.outputs = {}

        self.pos = None

        self.dependencies = []

        self.paramsFolded = True
        self.outputsFolded = True
        self.active = True

    def todict(self):
        return {k: v for k, v in list(self.__dict__.items()) if not k.startswith("_")}

    @property
    def algorithm(self):
        if self._algInstance is None:
            self._algInstance = algList.getAlgorithm(self.consoleName).getCopy()
        return self._algInstance

    def setName(self, model):
        if self.name is None:
            i = 1
            name = self.consoleName + "_" + str(i)
            while name in model.algs:
                i += 1
                name = self.consoleName + "_" + str(i)
            self.name = name

    def getOutputType(self, outputName):
        output = self.algorithm.getOutputFromName(outputName)
        return "output " + output.__class__.__name__.split(".")[-1][6:].lower()

    def toPython(self):
        s = []
        params = []
        for param in self.algorithm.parameters:
            value = self.params[param.name]

            def _toString(v):
                if isinstance(v, (ValueFromInput, ValueFromOutput)):
                    return v.asPythonParameter()
                elif isinstance(v, str):
                    return "\\n".join(("'%s'" % v).splitlines())
                elif isinstance(v, list):
                    return "[%s]" % ",".join([_toString(val) for val in v])
                else:
                    return str(value)
            params.append(_toString(value))
        for out in self.algorithm.outputs:
            if not out.hidden:
                if out.name in self.outputs:
                    params.append(safeName(self.outputs[out.name].description).lower())
                else:
                    params.append(str(None))
        s.append("outputs_%s=processing.runalg('%s', %s)" % (self.name, self.consoleName, ",".join(params)))
        return s


class ValueFromInput(object):

    def __init__(self, name=""):
        self.name = name

    def todict(self):
        return self.__dict__

    def __str__(self):
        return self.name

    def __eq__(self, other):
        try:
            return self.name == other.name
        except:
            return False

    def asPythonParameter(self):
        return self.name


class ValueFromOutput(object):

    def __init__(self, alg="", output=""):
        self.alg = alg
        self.output = output

    def todict(self):
        return self.__dict__

    def __eq__(self, other):
        try:
            return self.alg == other.alg and self.output == other.output
        except:
            return False

    def __str__(self):
        return self.alg + ":" + self.output

    def asPythonParameter(self):
        return "outputs_%s['%s']" % (self.alg, self.output)


class CompoundValue(object):

    def __init__(self, values=[], definition=""):
        self.values = values
        self.definition = definition

    def todict(self):
        return self.__dict__

    def __eq__(self, other):
        try:
            return self.values == other.values and self.definition == other.definition
        except:
            return False

    def __str__(self):
        return self.definition

    def asPythonParameter(self):
        return ""  # TODO


class ModelerAlgorithm(GeoAlgorithm):

    CANVAS_SIZE = 4000

    def getCopy(self):
        newone = ModelerAlgorithm()
        newone.provider = self.provider

        newone.algs = {}
        for algname, alg in self.algs.items():
            newone.algs[algname] = Algorithm()
            newone.algs[algname].__dict__.update(copy.deepcopy(alg.todict()))
        newone.inputs = copy.deepcopy(self.inputs)
        newone.defineCharacteristics()
        newone.name = self.name
        newone.group = self.group
        newone.descriptionFile = self.descriptionFile
        newone.helpContent = copy.deepcopy(self.helpContent)
        return newone

    def __init__(self):
        self.name = self.tr('Model', 'ModelerAlgorithm')
        # The dialog where this model is being edited
        self.modelerdialog = None
        self.descriptionFile = None
        self.helpContent = {}

        # Geoalgorithms in this model. A dict of Algorithm objects, with names as keys
        self.algs = {}

        # Input parameters. A dict of Input objects, with names as keys
        self.inputs = {}
        GeoAlgorithm.__init__(self)

    def getIcon(self):
        return QgsApplication.getThemeIcon("/processingModel.svg")

    def defineCharacteristics(self):
        classes = [ParameterRaster, ParameterVector, ParameterTable, ParameterTableField,
                   ParameterBoolean, ParameterString, ParameterNumber]
        self.parameters = []
        for c in classes:
            for inp in list(self.inputs.values()):
                if isinstance(inp.param, c):
                    self.parameters.append(inp.param)
        for inp in list(self.inputs.values()):
            if inp.param not in self.parameters:
                self.parameters.append(inp.param)
        self.parameters.sort(key=attrgetter("description"))

        self.outputs = []
        for alg in list(self.algs.values()):
            if alg.active:
                for out in alg.outputs:
                    modelOutput = copy.deepcopy(alg.algorithm.getOutputFromName(out))
                    modelOutput.name = self.getSafeNameForOutput(alg.name, out)
                    modelOutput.description = alg.outputs[out].description
                    self.outputs.append(modelOutput)
        self.outputs.sort(key=attrgetter("description"))

    def addParameter(self, param):
        self.inputs[param.param.name] = param

    def updateParameter(self, param):
        self.inputs[param.name].param = param

    def addAlgorithm(self, alg):
        name = self.getNameForAlgorithm(alg)
        alg.name = name
        self.algs[name] = alg

    def getNameForAlgorithm(self, alg):
        i = 1
        while alg.consoleName.upper().replace(":", "") + "_" + str(i) in list(self.algs.keys()):
            i += 1
        return alg.consoleName.upper().replace(":", "") + "_" + str(i)

    def updateAlgorithm(self, alg):
        alg.pos = self.algs[alg.name].pos
        alg.paramsFolded = self.algs[alg.name].paramsFolded
        alg.outputsFolded = self.algs[alg.name].outputsFolded
        self.algs[alg.name] = alg

        from processing.modeler.ModelerGraphicItem import ModelerGraphicItem
        for i, out in enumerate(alg.outputs):
            alg.outputs[out].pos = (alg.outputs[out].pos or
                                    alg.pos + QPointF(
                ModelerGraphicItem.BOX_WIDTH,
                (i + 1.5) * ModelerGraphicItem.BOX_HEIGHT))

    def removeAlgorithm(self, name):
        """Returns True if the algorithm could be removed, False if
        others depend on it and could not be removed.
        """
        if self.hasDependencies(name):
            return False
        del self.algs[name]
        self.modelerdialog.hasChanged = True
        return True

    def removeParameter(self, name):
        """Returns True if the parameter could be removed, False if
        others depend on it and could not be removed.
        """
        if self.hasDependencies(name):
            return False
        del self.inputs[name]
        self.modelerdialog.hasChanged = True
        return True

    def hasDependencies(self, name):
        """This method returns True if some other element depends on
        the passed one.
        """
        for alg in list(self.algs.values()):
            for value in list(alg.params.values()):
                if value is None:
                    continue
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, ValueFromInput):
                            if v.name == name:
                                return True
                        elif isinstance(v, ValueFromOutput):
                            if v.alg == name:
                                return True
                if isinstance(value, ValueFromInput):
                    if value.name == name:
                        return True
                elif isinstance(value, ValueFromOutput):
                    if value.alg == name:
                        return True
            if alg.name != name:
                for dep in alg.dependencies:
                    if (dep == name):
                        return True
        return False

    def getDependsOnAlgorithms(self, name):
        """This method returns a list with names of algorithms
        a given one depends on.
        """
        alg = self.algs[name]
        algs = set()
        algs.update(set(alg.dependencies))
        for value in list(alg.params.values()):
            if value is None:
                continue
            if isinstance(value, CompoundValue):
                for v in value.values:
                    if isinstance(v, ValueFromOutput):
                        algs.add(v.alg)
                        algs.update(self.getDependsOnAlgorithms(v.alg))
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, ValueFromOutput):
                        algs.add(v.alg)
                        algs.update(self.getDependsOnAlgorithms(v.alg))
            elif isinstance(value, ValueFromOutput):
                algs.add(value.alg)
                algs.update(self.getDependsOnAlgorithms(value.alg))

        return algs

    def getDependentAlgorithms(self, name):
        """This method returns a list with the names of algorithms
        depending on a given one. It includes the algorithm itself
        """
        algs = set()
        algs.add(name)
        for alg in list(self.algs.values()):
            for value in list(alg.params.values()):
                if value is None:
                    continue
                if isinstance(value, list):
                    for v in value:
                        if isinstance(v, ValueFromOutput) and v.alg == name:
                            algs.update(self.getDependentAlgorithms(alg.name))
                elif isinstance(value, ValueFromOutput) and value.alg == name:
                    algs.update(self.getDependentAlgorithms(alg.name))

        return algs

    def setPositions(self, paramPos, algPos, outputsPos):
        for param, pos in list(paramPos.items()):
            self.inputs[param].pos = pos
        for alg, pos in list(algPos.items()):
            self.algs[alg].pos = pos
        for alg, positions in list(outputsPos.items()):
            for output, pos in list(positions.items()):
                self.algs[alg].outputs[output].pos = pos

    def prepareAlgorithm(self, alg):
        algInstance = alg.algorithm
        for param in algInstance.parameters:
            if not param.hidden:
                if param.name in alg.params:
                    value = self.resolveValue(alg.params[param.name], param)
                else:
                    if iface is not None:
                        iface.messageBar().pushMessage(self.tr("Warning"),
                                                       self.tr("Parameter %s in algorithm %s in the model is run with default value! Edit the model to make sure that this is correct.") % (param.name, alg.name),
                                                       QgsMessageBar.WARNING, 4)
                    value = param.default
                # We allow unexistent filepaths, since that allows
                # algorithms to skip some conversion routines
                if not param.setValue(value) and not isinstance(param,
                                                                ParameterDataObject):
                    raise GeoAlgorithmExecutionException(
                        self.tr('Wrong value %s for %s %s', 'ModelerAlgorithm')
                        % (value, param.__class__.__name__, param.name))

        for out in algInstance.outputs:
            if not out.hidden:
                if out.name in alg.outputs:
                    name = self.getSafeNameForOutput(alg.name, out.name)
                    modelOut = self.getOutputFromName(name)
                    if modelOut:
                        out.value = modelOut.value
                else:
                    out.value = None

        return algInstance

    def deactivateAlgorithm(self, algName):
        dependent = self.getDependentAlgorithms(algName)
        for alg in dependent:
            self.algs[alg].active = False

    def activateAlgorithm(self, algName):
        parents = self.getDependsOnAlgorithms(algName)
        for alg in parents:
            if not self.algs[alg].active:
                return False
        self.algs[algName].active = True
        return True

    def getSafeNameForOutput(self, algName, outName):
        return outName + '_ALG' + algName

    def resolveValue(self, value, param):
        if value is None:
            v = None
        if isinstance(value, list):
            v = ";".join([self.resolveValue(v, param) for v in value])
        elif isinstance(value, CompoundValue):
            v = self.resolveValue(value.definition, param)
        elif isinstance(value, ValueFromInput):
            v = self.getParameterFromName(value.name).value
        elif isinstance(value, ValueFromOutput):
            v = self.algs[value.alg].algorithm.getOutputFromName(value.output).value
        else:
            v = value
        return param.evaluateForModeler(v, self)

    def processAlgorithm(self, feedback):
        executed = []
        toExecute = [alg for alg in list(self.algs.values()) if alg.active]
        while len(executed) < len(toExecute):
            for alg in toExecute:
                if alg.name not in executed:
                    canExecute = True
                    required = self.getDependsOnAlgorithms(alg.name)
                    for requiredAlg in required:
                        if requiredAlg != alg.name and requiredAlg not in executed:
                            canExecute = False
                            break
                    if canExecute:
                        try:
                            feedback.pushDebugInfo(
                                self.tr('Prepare algorithm: %s', 'ModelerAlgorithm') % alg.name)
                            self.prepareAlgorithm(alg)
                            feedback.setProgressText(
                                self.tr('Running %s [%i/%i]', 'ModelerAlgorithm') % (alg.description, len(executed) + 1, len(toExecute)))
                            feedback.pushDebugInfo('Parameters: ' + ', '.join([str(p).strip()
                                                                               + '=' + str(p.value) for p in alg.algorithm.parameters]))
                            t0 = time.time()
                            alg.algorithm.execute(feedback, self)
                            dt = time.time() - t0

                            # copy algorithm output value(s) back to model in case the algorithm modified those
                            for out in alg.algorithm.outputs:
                                if not out.hidden:
                                    if out.name in alg.outputs:
                                        modelOut = self.getOutputFromName(self.getSafeNameForOutput(alg.name, out.name))
                                        if modelOut:
                                            modelOut.value = out.value

                            executed.append(alg.name)
                            feedback.pushDebugInfo(
                                self.tr('OK. Execution took %0.3f ms (%i outputs).', 'ModelerAlgorithm') % (dt, len(alg.algorithm.outputs)))
                        except GeoAlgorithmExecutionException as e:
                            feedback.pushDebugInfo(self.tr('Failed', 'ModelerAlgorithm'))
                            raise GeoAlgorithmExecutionException(
                                self.tr('Error executing algorithm %s\n%s', 'ModelerAlgorithm') % (alg.description, e.msg))

        feedback.pushDebugInfo(
            self.tr('Model processed ok. Executed %i algorithms total', 'ModelerAlgorithm') % len(executed))

    def getAsCommand(self):
        if self.descriptionFile:
            return GeoAlgorithm.getAsCommand(self)
        else:
            return None

    def commandLineName(self):
        if self.descriptionFile is None:
            return ''
        else:
            return 'modeler:' + os.path.basename(self.descriptionFile)[:-6].lower()

    def checkBeforeOpeningParametersDialog(self):
        for alg in list(self.algs.values()):
            algInstance = algList.getAlgorithm(alg.consoleName)
            if algInstance is None:
                return "The model you are trying to run contains an algorithm that is not available: <i>%s</i>" % alg.consoleName

    def setModelerView(self, dialog):
        self.modelerdialog = dialog

    def updateModelerView(self):
        if self.modelerdialog:
            self.modelerdialog.repaintModel()

    def help(self):
        try:
            return True, getHtmlFromDescriptionsDict(self, self.helpContent)
        except:
            return False, None

    def shortHelp(self):
        if 'ALG_DESC' in self.helpContent:
            return self._formatHelp(str(self.helpContent['ALG_DESC']))
        return None

    def getParameterDescriptions(self):
        descs = {}
        descriptions = self.helpContent
        for param in self.parameters:
            if param.name in descriptions:
                descs[param.name] = str(descriptions[param.name])
        return descs

    def todict(self):
        keys = ["inputs", "group", "name", "algs", "helpContent"]
        return {k: v for k, v in list(self.__dict__.items()) if k in keys}

    def toJson(self):
        def todict(o):
            if isinstance(o, QPointF):
                return {"class": "point", "values": {"x": o.x(), "y": o.y()}}
            try:
                d = o.todict()
                return {"class": o.__class__.__module__ + "." + o.__class__.__name__, "values": d}
            except Exception:
                pass
        return json.dumps(self, default=todict, indent=4)

    @staticmethod
    def fromJson(s):
        def fromdict(d):
            try:
                fullClassName = d["class"]
                if isinstance(fullClassName, str):
                    tokens = fullClassName.split(".")
                else:
                    tokens = fullClassName.__class__.__name__.split(".")
                className = tokens[-1]
                moduleName = ".".join(tokens[:-1])
                values = d["values"]
                if className == "point":
                    return QPointF(values["x"], values["y"])

                def _import(name):
                    __import__(name)
                    return sys.modules[name]

                if moduleName.startswith("processing.parameters"):
                    moduleName = "processing.core.parameters"
                module = _import(moduleName)
                clazz = getattr(module, className)
                instance = clazz()
                for k, v in list(values.items()):
                    instance.__dict__[k] = v
                return instance
            except KeyError:
                return d
            except Exception as e:
                raise e
        try:
            model = json.loads(s, object_hook=fromdict)
        except Exception as e:
            raise WrongModelException(e.args[0])
        return model

    @staticmethod
    def fromFile(filename):
        with open(filename) as f:
            s = f.read()
        alg = ModelerAlgorithm.fromJson(s)
        alg.descriptionFile = filename
        return alg

    def toPython(self):
        s = ['##%s=name' % self.name]
        for param in list(self.inputs.values()):
            s.append(param.param.getAsScriptCode())
        for alg in list(self.algs.values()):
            for name, out in list(alg.outputs.items()):
                s.append('##%s=%s' % (safeName(out.description).lower(), alg.getOutputType(name)))

        executed = []
        toExecute = [alg for alg in list(self.algs.values()) if alg.active]
        while len(executed) < len(toExecute):
            for alg in toExecute:
                if alg.name not in executed:
                    canExecute = True
                    required = self.getDependsOnAlgorithms(alg.name)
                    for requiredAlg in required:
                        if requiredAlg != alg.name and requiredAlg not in executed:
                            canExecute = False
                            break
                    if canExecute:
                        s.extend(alg.toPython())
                        executed.append(alg.name)

        return '\n'.join(s)


def safeName(name):
    validChars = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join(c for c in name.lower() if c in validChars)
