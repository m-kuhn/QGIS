# -*- coding: utf-8 -*-

"""
***************************************************************************
    AlgorithmsTest.py
    ---------------------
    Date                 : January 2016
    Copyright            : (C) 2016 by Matthias Kuhn
    Email                : matthias@opengis.ch
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
from builtins import zip
from builtins import str
from builtins import object

__author__ = 'Matthias Kuhn'
__date__ = 'January 2016'
__copyright__ = '(C) 2016, Matthias Kuhn'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = ':%H$'


import qgis  # NOQA switch sip api

import os
import yaml
import nose2
import gdal
import shutil
import glob
import hashlib
import tempfile

from osgeo.gdalconst import GA_ReadOnly
from numpy import nan_to_num

import processing
from processing.modeler.ModelerAlgorithmProvider import ModelerAlgorithmProvider
from processing.algs.qgis.QGISAlgorithmProvider import QGISAlgorithmProvider
from processing.algs.grass7.Grass7AlgorithmProvider import Grass7AlgorithmProvider
from processing.algs.lidar.LidarToolsAlgorithmProvider import LidarToolsAlgorithmProvider
from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider
from processing.algs.otb.OTBAlgorithmProvider import OTBAlgorithmProvider
from processing.algs.r.RAlgorithmProvider import RAlgorithmProvider
from processing.algs.saga.SagaAlgorithmProvider import SagaAlgorithmProvider
from processing.script.ScriptAlgorithmProvider import ScriptAlgorithmProvider
from processing.preconfigured.PreconfiguredAlgorithmProvider import PreconfiguredAlgorithmProvider


from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsProject

from qgis.testing import _UnexpectedSuccess

from utilities import unitTestDataPath


def processingTestDataPath():
    return os.path.join(os.path.dirname(__file__), 'testdata')


class AlgorithmsTest(object):

    in_place_layers = {}

    def test_algorithms(self):
        """
        This is the main test function. All others will be executed based on the definitions in testdata/algorithm_tests.yaml
        """
        ver = processing.version()
        with open(os.path.join(processingTestDataPath(), self.test_definition_file()), 'r') as stream:
            algorithm_tests = yaml.load(stream)

        for algtest in algorithm_tests['tests']:
            yield self.check_algorithm, algtest['name'], algtest

    def check_algorithm(self, name, defs):
        """
        Will run an algorithm definition and check if it generates the expected result
        :param name: The identifier name used in the test output heading
        :param defs: A python dict containing a test algorithm definition
        """
        QgsProject.instance().removeAllMapLayers()

        params = self.load_params(defs['params'])

        alg = processing.Processing.getAlgorithm(defs['algorithm']).getCopy()

        if isinstance(params, list):
            for param in zip(alg.parameters, params):
                param[0].setValue(param[1])
        else:
            for k, p in list(params.items()):
                alg.setParameterValue(k, p)

        for r, p in list(defs['results'].items()):
            alg.setOutputValue(r, self.load_result_param(p))

        expectFailure = False
        if 'expectedFailure' in defs:
            exec(('\n'.join(defs['expectedFailure'][:-1])), globals(), locals())
            expectFailure = eval(defs['expectedFailure'][-1])

        if expectFailure:
            try:
                alg.execute()
                self.check_results(alg.getOutputValuesAsDictionary(), defs['params'], defs['results'])
            except Exception:
                pass
            else:
                raise _UnexpectedSuccess
        else:
            alg.execute()
            self.check_results(alg.getOutputValuesAsDictionary(), defs['params'], defs['results'])

    def load_params(self, params):
        """
        Loads an array of parameters
        """
        if isinstance(params, list):
            return [self.load_param(p) for p in params]
        elif isinstance(params, dict):
            return {key: self.load_param(p, key) for key, p in list(params.items())}
        else:
            return params

    def load_param(self, param, id=None):
        """
        Loads a parameter. If it's not a map, the parameter will be returned as-is. If it is a map, it will process the
        parameter based on its key `type` and return the appropriate parameter to pass to the algorithm.
        """
        try:
            if param['type'] in ('vector', 'raster', 'table'):
                return self.load_layer(id, param)
            elif param['type'] == 'multi':
                return [self.load_param(p) for p in param['params']]
            elif param['type'] == 'file':
                return self.filepath_from_param(param)
            elif param['type'] == 'interpolation':
                prefix = processingTestDataPath()
                tmp = ''
                for r in param['name'].split(';'):
                    v = r.split(',')
                    tmp += '{},{},{},{};'.format(os.path.join(prefix, v[0]),
                                                 v[1], v[2], v[3])
                return tmp[:-1]
        except TypeError:
            # No type specified, use whatever is there
            return param

        raise KeyError("Unknown type '{}' specified for parameter".format(param['type']))

    def load_result_param(self, param):
        """
        Loads a result parameter. Creates a temporary destination where the result should go to and returns this location
        so it can be sent to the algorithm as parameter.
        """
        if param['type'] in ['vector', 'file', 'table', 'regex']:
            outdir = tempfile.mkdtemp()
            self.cleanup_paths.append(outdir)
            basename = os.path.basename(param['name'])
            filepath = os.path.join(outdir, basename)
            return filepath
        elif param['type'] == 'rasterhash':
            outdir = tempfile.mkdtemp()
            self.cleanup_paths.append(outdir)
            basename = 'raster.tif'
            filepath = os.path.join(outdir, basename)
            return filepath

        raise KeyError("Unknown type '{}' specified for parameter".format(param['type']))

    def load_layer(self, id, param):
        """
        Loads a layer which was specified as parameter.
        """
        filepath = self.filepath_from_param(param)

        try:
            # check if alg modifies layer in place
            if param['in_place']:
                tmpdir = tempfile.mkdtemp()
                self.cleanup_paths.append(tmpdir)
                path, file_name = os.path.split(filepath)
                base, ext = os.path.splitext(file_name)
                for file in glob.glob(os.path.join(path, '{}.*'.format(base))):
                    shutil.copy(os.path.join(path, file), tmpdir)
                filepath = os.path.join(tmpdir, file_name)
                self.in_place_layers[id] = filepath
        except:
            pass

        if param['type'] in ('vector', 'table'):
            lyr = QgsVectorLayer(filepath, param['name'], 'ogr')
        elif param['type'] == 'raster':
            lyr = QgsRasterLayer(filepath, param['name'], 'gdal')

        self.assertTrue(lyr.isValid(), 'Could not load layer "{}"'.format(filepath))
        QgsProject.instance().addMapLayer(lyr)
        return lyr

    def filepath_from_param(self, param):
        """
        Creates a filepath from a param
        """
        prefix = processingTestDataPath()
        if 'location' in param and param['location'] == 'qgs':
            prefix = unitTestDataPath()

        return os.path.join(prefix, param['name'])

    def check_results(self, results, params, expected):
        """
        Checks if result produced by an algorithm matches with the expected specification.
        """
        for id, expected_result in list(expected.items()):
            if expected_result['type'] in ('vector', 'table'):
                expected_lyr = self.load_layer(id, expected_result)
                if 'in_place_result' in expected_result:
                    result_lyr = QgsVectorLayer(self.in_place_layers[id], id, 'ogr')
                else:
                    try:
                        results[id]
                    except KeyError as e:
                        raise KeyError('Expected result {} does not exist in {}'.format(str(e), list(results.keys())))

                    result_lyr = QgsVectorLayer(results[id], id, 'ogr')

                compare = expected_result.get('compare', {})

                self.assertLayersEqual(expected_lyr, result_lyr, compare=compare)

            elif 'rasterhash' == expected_result['type']:
                dataset = gdal.Open(results[id], GA_ReadOnly)
                dataArray = nan_to_num(dataset.ReadAsArray(0))
                strhash = hashlib.sha224(dataArray.data).hexdigest()

                self.assertEqual(strhash, expected_result['hash'])
            elif 'file' == expected_result['type']:
                expected_filepath = self.filepath_from_param(expected_result)
                result_filepath = results[id]

                self.assertFilesEqual(expected_filepath, result_filepath)
            elif 'regex' == expected_result['type']:
                with open(results[id], 'r') as file:
                    data = file.read()

                for rule in expected_result.get('rules', []):
                    self.assertRegexpMatches(data, rule)


if __name__ == '__main__':
    nose2.main()
