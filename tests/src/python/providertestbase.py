# -*- coding: utf-8 -*-
"""QGIS Unit test utils for provider tests.

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

from builtins import str
from builtins import object
__author__ = 'Matthias Kuhn'
__date__ = '2015-04-27'
__copyright__ = 'Copyright 2015, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from qgis.core import (
    QgsRectangle,
    QgsFeatureRequest,
    QgsFeature,
    QgsGeometry,
    QgsAbstractFeatureIterator,
    QgsExpressionContextScope,
    QgsExpressionContext,
    QgsVectorDataProvider,
    NULL
)

from utilities import(
    compareWkt
)


class ProviderTestCase(object):

    '''
        This is a collection of tests for vector data providers and kept generic.
        To make use of it, subclass it and set self.provider to a provider you want to test.
        Make sure that your provider uses the default dataset by converting one of the provided datasets from the folder
        tests/testdata/provider to a dataset your provider is able to handle.

        To test expression compilation, add the methods `enableCompiler()` and `disableCompiler()` to your subclass.
        If these methods are present, the tests will ensure that the result of server side and client side expression
        evaluation are equal.
    '''

    def testGetFeatures(self, provider=None, extra_features=[], skip_features=[], changed_attributes={}, changed_geometries={}):
        """ Test that expected results are returned when fetching all features """

        # IMPORTANT - we do not use `for f in provider.getFeatures()` as we are also
        # testing that existing attributes & geometry in f are overwritten correctly
        # (for f in ... uses a new QgsFeature for every iteration)

        if not provider:
            provider = self.provider

        it = provider.getFeatures()
        f = QgsFeature()
        attributes = {}
        geometries = {}
        while it.nextFeature(f):
            # expect feature to be valid
            self.assertTrue(f.isValid())
            # split off the first 5 attributes only - some provider test datasets will include
            # additional attributes which we ignore
            attrs = f.attributes()[0:5]
            # force the num_char attribute to be text - some providers (e.g., delimited text) will
            # automatically detect that this attribute contains numbers and set it as a numeric
            # field
            attrs[4] = str(attrs[4])
            attributes[f['pk']] = attrs
            geometries[f['pk']] = f.hasGeometry() and f.geometry().exportToWkt()

        expected_attributes = {5: [5, -200, NULL, 'NuLl', '5'],
                               3: [3, 300, 'Pear', 'PEaR', '3'],
                               1: [1, 100, 'Orange', 'oranGe', '1'],
                               2: [2, 200, 'Apple', 'Apple', '2'],
                               4: [4, 400, 'Honey', 'Honey', '4']}

        expected_geometries = {1: 'Point (-70.332 66.33)',
                               2: 'Point (-68.2 70.8)',
                               3: None,
                               4: 'Point(-65.32 78.3)',
                               5: 'Point(-71.123 78.23)'}
        for f in extra_features:
            expected_attributes[f[0]] = f.attributes()
            if f.hasGeometry():
                expected_geometries[f[0]] = f.geometry().exportToWkt()
            else:
                expected_geometries[f[0]] = None

        for i in skip_features:
            del expected_attributes[i]
            del expected_geometries[i]
        for i, a in changed_attributes.items():
            for attr_idx, v in a.items():
                expected_attributes[i][attr_idx] = v
        for i, g, in changed_geometries.items():
            if g:
                expected_geometries[i] = g.exportToWkt()
            else:
                expected_geometries[i] = None

        self.assertEqual(attributes, expected_attributes, 'Expected {}, got {}'.format(expected_attributes, attributes))

        self.assertEqual(len(expected_geometries), len(geometries))

        for pk, geom in list(expected_geometries.items()):
            if geom:
                assert compareWkt(geom, geometries[pk]), "Geometry {} mismatch Expected:\n{}\nGot:\n{}\n".format(pk, geom, geometries[pk])
            else:
                self.assertFalse(geometries[pk], 'Expected null geometry for {}'.format(pk))

    def uncompiledFilters(self):
        """ Individual derived provider tests should override this to return a list of expressions which
        cannot be compiled """
        return set()

    def partiallyCompiledFilters(self):
        """ Individual derived provider tests should override this to return a list of expressions which
        should be partially compiled """
        return set()

    def assert_query(self, provider, expression, expected):
        request = QgsFeatureRequest().setFilterExpression(expression).setFlags(QgsFeatureRequest.NoGeometry)
        result = set([f['pk'] for f in provider.getFeatures(request)])
        assert set(expected) == result, 'Expected {} and got {} when testing expression "{}"'.format(set(expected), result, expression)
        self.assertTrue(all(f.isValid() for f in provider.getFeatures(request)))

        if self.compiled:
            # Check compilation status
            it = provider.getFeatures(QgsFeatureRequest().setFilterExpression(expression))

            if expression in self.uncompiledFilters():
                self.assertEqual(it.compileStatus(), QgsAbstractFeatureIterator.NoCompilation)
            elif expression in self.partiallyCompiledFilters():
                self.assertEqual(it.compileStatus(), QgsAbstractFeatureIterator.PartiallyCompiled)
            else:
                self.assertEqual(it.compileStatus(), QgsAbstractFeatureIterator.Compiled)

        # Also check that filter works when referenced fields are not being retrieved by request
        result = set([f['pk'] for f in provider.getFeatures(QgsFeatureRequest().setFilterExpression(expression).setSubsetOfAttributes([0]))])
        assert set(expected) == result, 'Expected {} and got {} when testing expression "{}" using empty attribute subset'.format(set(expected), result, expression)

    def runGetFeatureTests(self, provider):
        assert len([f for f in provider.getFeatures()]) == 5
        self.assert_query(provider, 'name ILIKE \'QGIS\'', [])
        self.assert_query(provider, '"name" IS NULL', [5])
        self.assert_query(provider, '"name" IS NOT NULL', [1, 2, 3, 4])
        self.assert_query(provider, '"name" NOT LIKE \'Ap%\'', [1, 3, 4])
        self.assert_query(provider, '"name" NOT ILIKE \'QGIS\'', [1, 2, 3, 4])
        self.assert_query(provider, '"name" NOT ILIKE \'pEAR\'', [1, 2, 4])
        self.assert_query(provider, 'name = \'Apple\'', [2])
        self.assert_query(provider, 'name <> \'Apple\'', [1, 3, 4])
        self.assert_query(provider, 'name = \'apple\'', [])
        self.assert_query(provider, '"name" <> \'apple\'', [1, 2, 3, 4])
        self.assert_query(provider, '(name = \'Apple\') is not null', [1, 2, 3, 4])
        self.assert_query(provider, 'name LIKE \'Apple\'', [2])
        self.assert_query(provider, 'name LIKE \'aPple\'', [])
        self.assert_query(provider, 'name ILIKE \'aPple\'', [2])
        self.assert_query(provider, 'name ILIKE \'%pp%\'', [2])
        self.assert_query(provider, 'cnt > 0', [1, 2, 3, 4])
        self.assert_query(provider, '-cnt > 0', [5])
        self.assert_query(provider, 'cnt < 0', [5])
        self.assert_query(provider, '-cnt < 0', [1, 2, 3, 4])
        self.assert_query(provider, 'cnt >= 100', [1, 2, 3, 4])
        self.assert_query(provider, 'cnt <= 100', [1, 5])
        self.assert_query(provider, 'pk IN (1, 2, 4, 8)', [1, 2, 4])
        self.assert_query(provider, 'cnt = 50 * 2', [1])
        self.assert_query(provider, 'cnt = 150 / 1.5', [1])
        self.assert_query(provider, 'cnt = 1000 / 10', [1])
        self.assert_query(provider, 'cnt = 1000/11+10', []) # checks that provider isn't rounding int/int
        self.assert_query(provider, 'pk = 9 // 4', [2]) # int division
        self.assert_query(provider, 'cnt = 99 + 1', [1])
        self.assert_query(provider, 'cnt = 101 - 1', [1])
        self.assert_query(provider, 'cnt - 1 = 99', [1])
        self.assert_query(provider, '-cnt - 1 = -101', [1])
        self.assert_query(provider, '-(-cnt) = 100', [1])
        self.assert_query(provider, '-(cnt) = -(100)', [1])
        self.assert_query(provider, 'cnt + 1 = 101', [1])
        self.assert_query(provider, 'cnt = 1100 % 1000', [1])
        self.assert_query(provider, '"name" || \' \' || "name" = \'Orange Orange\'', [1])
        self.assert_query(provider, '"name" || \' \' || "cnt" = \'Orange 100\'', [1])
        self.assert_query(provider, '\'x\' || "name" IS NOT NULL', [1, 2, 3, 4])
        self.assert_query(provider, '\'x\' || "name" IS NULL', [5])
        self.assert_query(provider, 'cnt = 10 ^ 2', [1])
        self.assert_query(provider, '"name" ~ \'[OP]ra[gne]+\'', [1])
        self.assert_query(provider, '"name"="name2"', [2, 4])  # mix of matched and non-matched case sensitive names
        self.assert_query(provider, 'true', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'false', [])

        # Three value logic
        self.assert_query(provider, 'false and false', [])
        self.assert_query(provider, 'false and true', [])
        self.assert_query(provider, 'false and NULL', [])
        self.assert_query(provider, 'true and false', [])
        self.assert_query(provider, 'true and true', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'true and NULL', [])
        self.assert_query(provider, 'NULL and false', [])
        self.assert_query(provider, 'NULL and true', [])
        self.assert_query(provider, 'NULL and NULL', [])
        self.assert_query(provider, 'false or false', [])
        self.assert_query(provider, 'false or true', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'false or NULL', [])
        self.assert_query(provider, 'true or false', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'true or true', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'true or NULL', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'NULL or false', [])
        self.assert_query(provider, 'NULL or true', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'NULL or NULL', [])
        self.assert_query(provider, 'not true', [])
        self.assert_query(provider, 'not false', [1, 2, 3, 4, 5])
        self.assert_query(provider, 'not null', [])

        # not
        self.assert_query(provider, 'not name = \'Apple\'', [1, 3, 4])
        self.assert_query(provider, 'not name IS NULL', [1, 2, 3, 4])
        self.assert_query(provider, 'not name = \'Apple\' or name = \'Apple\'', [1, 2, 3, 4])
        self.assert_query(provider, 'not name = \'Apple\' or not name = \'Apple\'', [1, 3, 4])
        self.assert_query(provider, 'not name = \'Apple\' and pk = 4', [4])
        self.assert_query(provider, 'not name = \'Apple\' and not pk = 4', [1, 3])
        self.assert_query(provider, 'not pk IN (1, 2, 4, 8)', [3, 5])

        # type conversion - QGIS expressions do not mind that we are comparing a string
        # against numeric literals
        self.assert_query(provider, 'num_char IN (2, 4, 5)', [2, 4, 5])

        #function
        self.assert_query(provider, 'sqrt(pk) >= 2', [4, 5])
        self.assert_query(provider, 'radians(cnt) < 2', [1, 5])
        self.assert_query(provider, 'degrees(pk) <= 200', [1, 2, 3])
        self.assert_query(provider, 'abs(cnt) <= 200', [1, 2, 5])
        self.assert_query(provider, 'cos(pk) < 0', [2, 3, 4])
        self.assert_query(provider, 'sin(pk) < 0', [4, 5])
        self.assert_query(provider, 'tan(pk) < 0', [2, 3, 5])
        self.assert_query(provider, 'acos(-1) < pk', [4, 5])
        self.assert_query(provider, 'asin(1) < pk', [2, 3, 4, 5])
        self.assert_query(provider, 'atan(3.14) < pk', [2, 3, 4, 5])
        self.assert_query(provider, 'atan2(3.14, pk) < 1', [3, 4, 5])
        self.assert_query(provider, 'exp(pk) < 10', [1, 2])
        self.assert_query(provider, 'ln(pk) <= 1', [1, 2])
        self.assert_query(provider, 'log(3, pk) <= 1', [1, 2, 3])
        self.assert_query(provider, 'log10(pk) < 0.5', [1, 2, 3])
        self.assert_query(provider, 'round(3.14) <= pk', [3, 4, 5])
        self.assert_query(provider, 'round(0.314,1) * 10 = pk', [3])
        self.assert_query(provider, 'floor(3.14) <= pk', [3, 4, 5])
        self.assert_query(provider, 'ceil(3.14) <= pk', [4, 5])
        self.assert_query(provider, 'pk < pi()', [1, 2, 3])

        self.assert_query(provider, 'round(cnt / 66.67) <= 2', [1, 5])
        self.assert_query(provider, 'floor(cnt / 66.67) <= 2', [1, 2, 5])
        self.assert_query(provider, 'ceil(cnt / 66.67) <= 2', [1, 5])
        self.assert_query(provider, 'pk < pi() / 2', [1])
        self.assert_query(provider, 'pk = char(51)', [3])
        self.assert_query(provider, 'pk = coalesce(NULL,3,4)', [3])
        self.assert_query(provider, 'lower(name) = \'apple\'', [2])
        self.assert_query(provider, 'upper(name) = \'APPLE\'', [2])
        self.assert_query(provider, 'name = trim(\'   Apple   \')', [2])

        # geometry
        # azimuth and touches tests are deactivated because they do not pass for WFS provider
        #self.assert_query(provider, 'azimuth($geometry,geom_from_wkt( \'Point (-70 70)\')) < pi()', [1, 5])
        self.assert_query(provider, 'x($geometry) < -70', [1, 5])
        self.assert_query(provider, 'y($geometry) > 70', [2, 4, 5])
        self.assert_query(provider, 'xmin($geometry) < -70', [1, 5])
        self.assert_query(provider, 'ymin($geometry) > 70', [2, 4, 5])
        self.assert_query(provider, 'xmax($geometry) < -70', [1, 5])
        self.assert_query(provider, 'ymax($geometry) > 70', [2, 4, 5])
        self.assert_query(provider, 'disjoint($geometry,geom_from_wkt( \'Polygon ((-72.2 66.1, -65.2 66.1, -65.2 72.0, -72.2 72.0, -72.2 66.1))\'))', [4, 5])
        self.assert_query(provider, 'intersects($geometry,geom_from_wkt( \'Polygon ((-72.2 66.1, -65.2 66.1, -65.2 72.0, -72.2 72.0, -72.2 66.1))\'))', [1, 2])
        #self.assert_query(provider, 'touches($geometry,geom_from_wkt( \'Polygon ((-70.332 66.33, -65.32 66.33, -65.32 78.3, -70.332 78.3, -70.332 66.33))\'))', [1, 4])
        self.assert_query(provider, 'contains(geom_from_wkt( \'Polygon ((-72.2 66.1, -65.2 66.1, -65.2 72.0, -72.2 72.0, -72.2 66.1))\'),$geometry)', [1, 2])
        self.assert_query(provider, 'distance($geometry,geom_from_wkt( \'Point (-70 70)\')) > 7', [4, 5])
        self.assert_query(provider, 'intersects($geometry,geom_from_gml( \'<gml:Polygon srsName="EPSG:4326"><gml:outerBoundaryIs><gml:LinearRing><gml:coordinates>-72.2,66.1 -65.2,66.1 -65.2,72.0 -72.2,72.0 -72.2,66.1</gml:coordinates></gml:LinearRing></gml:outerBoundaryIs></gml:Polygon>\'))', [1, 2])

        # combination of an uncompilable expression and limit
        feature = next(self.vl.getFeatures('pk=4'))
        context = QgsExpressionContext()
        scope = QgsExpressionContextScope()
        scope.setVariable('parent', feature)
        context.appendScope(scope)

        request = QgsFeatureRequest()
        request.setExpressionContext(context)
        request.setFilterExpression('"pk" = attribute(@parent, \'pk\')')
        request.setLimit(1)

        values = [f['pk'] for f in self.vl.getFeatures(request)]
        self.assertEqual(values, [4])

    def runPolyGetFeatureTests(self, provider):
        assert len([f for f in provider.getFeatures()]) == 4

        # geometry
        self.assert_query(provider, 'x($geometry) < -70', [1])
        self.assert_query(provider, 'y($geometry) > 79', [1, 2])
        self.assert_query(provider, 'xmin($geometry) < -70', [1, 3])
        self.assert_query(provider, 'ymin($geometry) < 76', [3])
        self.assert_query(provider, 'xmax($geometry) > -68', [2, 3])
        self.assert_query(provider, 'ymax($geometry) > 80', [1, 2])
        self.assert_query(provider, 'area($geometry) > 10', [1])
        self.assert_query(provider, 'perimeter($geometry) < 12', [2, 3])
        self.assert_query(provider, 'relate($geometry,geom_from_wkt( \'Polygon ((-68.2 82.1, -66.95 82.1, -66.95 79.05, -68.2 79.05, -68.2 82.1))\')) = \'FF2FF1212\'', [1, 3])
        self.assert_query(provider, 'relate($geometry,geom_from_wkt( \'Polygon ((-68.2 82.1, -66.95 82.1, -66.95 79.05, -68.2 79.05, -68.2 82.1))\'), \'****F****\')', [1, 3])
        self.assert_query(provider, 'crosses($geometry,geom_from_wkt( \'Linestring (-68.2 82.1, -66.95 82.1, -66.95 79.05)\'))', [2])
        self.assert_query(provider, 'overlaps($geometry,geom_from_wkt( \'Polygon ((-68.2 82.1, -66.95 82.1, -66.95 79.05, -68.2 79.05, -68.2 82.1))\'))', [2])
        self.assert_query(provider, 'within($geometry,geom_from_wkt( \'Polygon ((-75.1 76.1, -75.1 81.6, -68.8 81.6, -68.8 76.1, -75.1 76.1))\'))', [1])
        self.assert_query(provider, 'overlaps(translate($geometry,-1,-1),geom_from_wkt( \'Polygon ((-75.1 76.1, -75.1 81.6, -68.8 81.6, -68.8 76.1, -75.1 76.1))\'))', [1])
        self.assert_query(provider, 'overlaps(buffer($geometry,1),geom_from_wkt( \'Polygon ((-75.1 76.1, -75.1 81.6, -68.8 81.6, -68.8 76.1, -75.1 76.1))\'))', [1, 3])
        self.assert_query(provider, 'intersects(centroid($geometry),geom_from_wkt( \'Polygon ((-74.4 78.2, -74.4 79.1, -66.8 79.1, -66.8 78.2, -74.4 78.2))\'))', [2])
        self.assert_query(provider, 'intersects(point_on_surface($geometry),geom_from_wkt( \'Polygon ((-74.4 78.2, -74.4 79.1, -66.8 79.1, -66.8 78.2, -74.4 78.2))\'))', [1, 2])
        self.assert_query(provider, 'distance($geometry,geom_from_wkt( \'Point (-70 70)\')) > 7', [1, 2])

    def testGetFeaturesUncompiled(self):
        self.compiled = False
        try:
            self.disableCompiler()
        except AttributeError:
            pass
        self.runGetFeatureTests(self.provider)
        if hasattr(self, 'poly_provider'):
            self.runPolyGetFeatureTests(self.poly_provider)

    def testPolyGetFeaturesCompiled(self):
        try:
            self.enableCompiler()
            self.compiled = True
            self.runGetFeatureTests(self.provider)
            if hasattr(self, 'poly_provider'):
                self.runPolyGetFeatureTests(self.poly_provider)
        except AttributeError:
            print('Provider does not support compiling')

    def testSubsetString(self):
        if not self.provider.supportsSubsetString():
            print('Provider does not support subset strings')
            return

        subset = self.getSubsetString()
        self.provider.setSubsetString(subset)
        self.assertEqual(self.provider.subsetString(), subset)
        result = set([f['pk'] for f in self.provider.getFeatures()])
        all_valid = (all(f.isValid() for f in self.provider.getFeatures()))
        self.provider.setSubsetString(None)

        expected = set([2, 3, 4])
        assert set(expected) == result, 'Expected {} and got {} when testing subset string {}'.format(set(expected), result, subset)
        self.assertTrue(all_valid)

        # Subset string AND filter rect
        self.provider.setSubsetString(subset)
        extent = QgsRectangle(-70, 70, -60, 75)
        request = QgsFeatureRequest().setFilterRect(extent)
        result = set([f['pk'] for f in self.provider.getFeatures(request)])
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        self.provider.setSubsetString(None)
        expected = set([2])
        assert set(expected) == result, 'Expected {} and got {} when testing subset string {}'.format(set(expected), result, subset)
        self.assertTrue(all_valid)

        # Subset string AND filter rect, version 2
        self.provider.setSubsetString(subset)
        extent = QgsRectangle(-71, 65, -60, 80)
        result = set([f['pk'] for f in self.provider.getFeatures(QgsFeatureRequest().setFilterRect(extent))])
        self.provider.setSubsetString(None)
        expected = set([2, 4])
        assert set(expected) == result, 'Expected {} and got {} when testing subset string {}'.format(set(expected), result, subset)

        # Subset string AND expression
        self.provider.setSubsetString(subset)
        request = QgsFeatureRequest().setFilterExpression('length("name")=5')
        result = set([f['pk'] for f in self.provider.getFeatures(request)])
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        self.provider.setSubsetString(None)
        expected = set([2, 4])
        assert set(expected) == result, 'Expected {} and got {} when testing subset string {}'.format(set(expected), result, subset)
        self.assertTrue(all_valid)

    def getSubsetString(self):
        """Individual providers may need to override this depending on their subset string formats"""
        return '"cnt" > 100 and "cnt" < 410'

    def getSubsetString2(self):
        """Individual providers may need to override this depending on their subset string formats"""
        return '"cnt" > 100 and "cnt" < 400'

    def testOrderByUncompiled(self):
        try:
            self.disableCompiler()
        except AttributeError:
            pass
        self.runOrderByTests()

    def testOrderByCompiled(self):
        try:
            self.enableCompiler()
            self.runOrderByTests()
        except AttributeError:
            print('Provider does not support compiling')

    def runOrderByTests(self):
        request = QgsFeatureRequest().addOrderBy('cnt')
        values = [f['cnt'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [-200, 100, 200, 300, 400])

        request = QgsFeatureRequest().addOrderBy('cnt', False)
        values = [f['cnt'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [400, 300, 200, 100, -200])

        request = QgsFeatureRequest().addOrderBy('name')
        values = [f['name'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, ['Apple', 'Honey', 'Orange', 'Pear', NULL])

        request = QgsFeatureRequest().addOrderBy('name', True, True)
        values = [f['name'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [NULL, 'Apple', 'Honey', 'Orange', 'Pear'])

        request = QgsFeatureRequest().addOrderBy('name', False)
        values = [f['name'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [NULL, 'Pear', 'Orange', 'Honey', 'Apple'])

        request = QgsFeatureRequest().addOrderBy('name', False, False)
        values = [f['name'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, ['Pear', 'Orange', 'Honey', 'Apple', NULL])

        # Case sensitivity
        request = QgsFeatureRequest().addOrderBy('name2')
        values = [f['name2'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, ['Apple', 'Honey', 'NuLl', 'oranGe', 'PEaR'])

        # Combination with LIMIT
        request = QgsFeatureRequest().addOrderBy('pk', False).setLimit(2)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [5, 4])

        # A slightly more complex expression
        request = QgsFeatureRequest().addOrderBy('pk*2', False)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [5, 4, 3, 2, 1])

        # Order reversing expression
        request = QgsFeatureRequest().addOrderBy('pk*-1', False)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [1, 2, 3, 4, 5])

        # Type dependent expression
        request = QgsFeatureRequest().addOrderBy('num_char*2', False)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [5, 4, 3, 2, 1])

        # Order by guaranteed to fail
        request = QgsFeatureRequest().addOrderBy('not a valid expression*', False)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(set(values), set([5, 4, 3, 2, 1]))

        # Multiple order bys and boolean
        request = QgsFeatureRequest().addOrderBy('pk > 2').addOrderBy('pk', False)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [2, 1, 5, 4, 3])

        # Multiple order bys, one bad, and a limit
        request = QgsFeatureRequest().addOrderBy('pk', False).addOrderBy('not a valid expression*', False).setLimit(2)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [5, 4])

        # Bad expression first
        request = QgsFeatureRequest().addOrderBy('not a valid expression*', False).addOrderBy('pk', False).setLimit(2)
        values = [f['pk'] for f in self.provider.getFeatures(request)]
        self.assertEqual(values, [5, 4])

        # Combination with subset of attributes
        request = QgsFeatureRequest().addOrderBy('num_char', False).setSubsetOfAttributes(['pk'], self.vl.fields())
        values = [f['pk'] for f in self.vl.getFeatures(request)]
        self.assertEqual(values, [5, 4, 3, 2, 1])

    def testGetFeaturesFidTests(self):
        fids = [f.id() for f in self.provider.getFeatures()]
        assert len(fids) == 5, 'Expected 5 features, got {} instead'.format(len(fids))
        for id in fids:
            features = [f for f in self.provider.getFeatures(QgsFeatureRequest().setFilterFid(id))]
            self.assertEqual(len(features), 1)
            feature = features[0]
            self.assertTrue(feature.isValid())

            result = [feature.id()]
            expected = [id]
            assert result == expected, 'Expected {} and got {} when testing for feature ID filter'.format(expected, result)

        # bad features
        it = self.provider.getFeatures(QgsFeatureRequest().setFilterFid(-99999999))
        feature = QgsFeature(5)
        feature.setValid(False)
        self.assertFalse(it.nextFeature(feature))
        self.assertFalse(feature.isValid())

    def testGetFeaturesFidsTests(self):
        fids = [f.id() for f in self.provider.getFeatures()]
        self.assertEqual(len(fids), 5)

        request = QgsFeatureRequest().setFilterFids([fids[0], fids[2]])
        result = set([f.id() for f in self.provider.getFeatures(request)])
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        expected = set([fids[0], fids[2]])
        assert result == expected, 'Expected {} and got {} when testing for feature IDs filter'.format(expected, result)
        self.assertTrue(all_valid)

        result = set([f.id() for f in self.provider.getFeatures(QgsFeatureRequest().setFilterFids([fids[1], fids[3], fids[4]]))])
        expected = set([fids[1], fids[3], fids[4]])
        assert result == expected, 'Expected {} and got {} when testing for feature IDs filter'.format(expected, result)

        #providers should ignore non-existant fids
        result = set([f.id() for f in self.provider.getFeatures(QgsFeatureRequest().setFilterFids([-101, fids[1], -102, fids[3], -103, fids[4], -104]))])
        expected = set([fids[1], fids[3], fids[4]])
        assert result == expected, 'Expected {} and got {} when testing for feature IDs filter'.format(expected, result)

        result = set([f.id() for f in self.provider.getFeatures(QgsFeatureRequest().setFilterFids([]))])
        expected = set([])
        assert result == expected, 'Expected {} and got {} when testing for feature IDs filter'.format(expected, result)

        # Rewind mid-way
        request = QgsFeatureRequest().setFilterFids([fids[1], fids[3], fids[4]])
        feature_it = self.provider.getFeatures(request)
        feature = QgsFeature()
        feature.setValid(True)
        self.assertTrue(feature_it.nextFeature(feature))
        self.assertIn(feature.id(), [fids[1], fids[3], fids[4]])
        first_feature = feature
        self.assertTrue(feature.isValid())
        # rewind
        self.assertTrue(feature_it.rewind())
        self.assertTrue(feature_it.nextFeature(feature))
        self.assertEqual(feature.id(), first_feature.id())
        self.assertTrue(feature.isValid())
        # grab all features
        self.assertTrue(feature_it.nextFeature(feature))
        self.assertTrue(feature_it.nextFeature(feature))
        # none left
        self.assertFalse(feature_it.nextFeature(feature))
        self.assertFalse(feature.isValid())

    def testGetFeaturesFilterRectTests(self):
        extent = QgsRectangle(-70, 67, -60, 80)
        request = QgsFeatureRequest().setFilterRect(extent)
        features = [f['pk'] for f in self.provider.getFeatures(request)]
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        assert set(features) == set([2, 4]), 'Got {} instead'.format(features)
        self.assertTrue(all_valid)

        # test with an empty rectangle
        extent = QgsRectangle()
        request = QgsFeatureRequest().setFilterRect(extent)
        features = [f['pk'] for f in self.provider.getFeatures(request)]
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        assert set(features) == set([1, 2, 3, 4, 5]), 'Got {} instead'.format(features)
        self.assertTrue(all_valid)

    def testGetFeaturesPolyFilterRectTests(self):
        """ Test fetching features from a polygon layer with filter rect"""
        try:
            if not self.poly_provider:
                return
        except:
            return

        extent = QgsRectangle(-73, 70, -63, 80)
        request = QgsFeatureRequest().setFilterRect(extent)
        features = [f['pk'] for f in self.poly_provider.getFeatures(request)]
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        # Some providers may return the exact intersection matches (2, 3) even without the ExactIntersect flag, so we accept that too
        assert set(features) == set([2, 3]) or set(features) == set([1, 2, 3]), 'Got {} instead'.format(features)
        self.assertTrue(all_valid)

        # Test with exact intersection
        request = QgsFeatureRequest().setFilterRect(extent).setFlags(QgsFeatureRequest.ExactIntersect)
        features = [f['pk'] for f in self.poly_provider.getFeatures(request)]
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        assert set(features) == set([2, 3]), 'Got {} instead'.format(features)
        self.assertTrue(all_valid)

        # test with an empty rectangle
        extent = QgsRectangle()
        features = [f['pk'] for f in self.provider.getFeatures(QgsFeatureRequest().setFilterRect(extent))]
        assert set(features) == set([1, 2, 3, 4, 5]), 'Got {} instead'.format(features)

    def testRectAndExpression(self):
        extent = QgsRectangle(-70, 67, -60, 80)
        request = QgsFeatureRequest().setFilterExpression('"cnt">200').setFilterRect(extent)
        result = set([f['pk'] for f in self.provider.getFeatures(request)])
        all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
        expected = [4]
        assert set(expected) == result, 'Expected {} and got {} when testing for combination of filterRect and expression'.format(set(expected), result)
        self.assertTrue(all_valid)

    def testGetFeaturesLimit(self):
        it = self.provider.getFeatures(QgsFeatureRequest().setLimit(2))
        features = [f['pk'] for f in it]
        assert len(features) == 2, 'Expected two features, got {} instead'.format(len(features))
        # fetch one feature
        feature = QgsFeature()
        assert not it.nextFeature(feature), 'Expected no feature after limit, got one'
        it.rewind()
        features = [f['pk'] for f in it]
        assert len(features) == 2, 'Expected two features after rewind, got {} instead'.format(len(features))
        it.rewind()
        assert it.nextFeature(feature), 'Expected feature after rewind, got none'
        it.rewind()
        features = [f['pk'] for f in it]
        assert len(features) == 2, 'Expected two features after rewind, got {} instead'.format(len(features))
        # test with expression, both with and without compilation
        try:
            self.disableCompiler()
        except AttributeError:
            pass
        it = self.provider.getFeatures(QgsFeatureRequest().setLimit(2).setFilterExpression('cnt <= 100'))
        features = [f['pk'] for f in it]
        assert set(features) == set([1, 5]), 'Expected [1,5] for expression and feature limit, Got {} instead'.format(features)
        try:
            self.enableCompiler()
        except AttributeError:
            pass
        it = self.provider.getFeatures(QgsFeatureRequest().setLimit(2).setFilterExpression('cnt <= 100'))
        features = [f['pk'] for f in it]
        assert set(features) == set([1, 5]), 'Expected [1,5] for expression and feature limit, Got {} instead'.format(features)
        # limit to more features than exist
        it = self.provider.getFeatures(QgsFeatureRequest().setLimit(3).setFilterExpression('cnt <= 100'))
        features = [f['pk'] for f in it]
        assert set(features) == set([1, 5]), 'Expected [1,5] for expression and feature limit, Got {} instead'.format(features)
        # limit to less features than possible
        it = self.provider.getFeatures(QgsFeatureRequest().setLimit(1).setFilterExpression('cnt <= 100'))
        features = [f['pk'] for f in it]
        assert 1 in features or 5 in features, 'Expected either 1 or 5 for expression and feature limit, Got {} instead'.format(features)

    def testMinValue(self):
        self.assertEqual(self.provider.minimumValue(1), -200)
        self.assertEqual(self.provider.minimumValue(2), 'Apple')

        subset = self.getSubsetString()
        self.provider.setSubsetString(subset)
        min_value = self.provider.minimumValue(1)
        self.provider.setSubsetString(None)
        self.assertEqual(min_value, 200)

    def testMaxValue(self):
        self.assertEqual(self.provider.maximumValue(1), 400)
        self.assertEqual(self.provider.maximumValue(2), 'Pear')

        subset = self.getSubsetString2()
        self.provider.setSubsetString(subset)
        max_value = self.provider.maximumValue(1)
        self.provider.setSubsetString(None)
        self.assertEqual(max_value, 300)

    def testExtent(self):
        reference = QgsGeometry.fromRect(
            QgsRectangle(-71.123, 66.33, -65.32, 78.3))
        provider_extent = QgsGeometry.fromRect(self.provider.extent())

        self.assertTrue(QgsGeometry.compare(provider_extent.asPolygon()[0], reference.asPolygon()[0], 0.00001))

    def testUnique(self):
        self.assertEqual(set(self.provider.uniqueValues(1)), set([-200, 100, 200, 300, 400]))
        assert set(['Apple', 'Honey', 'Orange', 'Pear', NULL]) == set(self.provider.uniqueValues(2)), 'Got {}'.format(set(self.provider.uniqueValues(2)))

        subset = self.getSubsetString2()
        self.provider.setSubsetString(subset)
        values = self.provider.uniqueValues(1)
        self.provider.setSubsetString(None)
        self.assertEqual(set(values), set([200, 300]))

    def testUniqueStringsMatching(self):
        self.assertEqual(set(self.provider.uniqueStringsMatching(2, 'a')), set(['Pear', 'Orange', 'Apple']))
        # test case insensitive
        self.assertEqual(set(self.provider.uniqueStringsMatching(2, 'A')), set(['Pear', 'Orange', 'Apple']))
        # test string ending in substring
        self.assertEqual(set(self.provider.uniqueStringsMatching(2, 'ney')), set(['Honey']))
        # test limit
        result = set(self.provider.uniqueStringsMatching(2, 'a', 2))
        self.assertEqual(len(result), 2)
        self.assertTrue(result.issubset(set(['Pear', 'Orange', 'Apple'])))

        assert set([u'Apple', u'Honey', u'Orange', u'Pear', NULL]) == set(self.provider.uniqueValues(2)), 'Got {}'.format(set(self.provider.uniqueValues(2)))

        subset = self.getSubsetString2()
        self.provider.setSubsetString(subset)
        values = self.provider.uniqueStringsMatching(2, 'a')
        self.provider.setSubsetString(None)
        self.assertEqual(set(values), set(['Pear', 'Apple']))

    def testFeatureCount(self):
        assert self.provider.featureCount() == 5, 'Got {}'.format(self.provider.featureCount())

        #Add a subset string and test feature count
        subset = self.getSubsetString()
        self.provider.setSubsetString(subset)
        count = self.provider.featureCount()
        self.provider.setSubsetString(None)
        assert count == 3, 'Got {}'.format(count)

    def testClosedIterators(self):
        """ Test behavior of closed iterators """

        # Test retrieving feature after closing iterator
        f_it = self.provider.getFeatures(QgsFeatureRequest())
        fet = QgsFeature()
        assert f_it.nextFeature(fet), 'Could not fetch feature'
        assert fet.isValid(), 'Feature is not valid'
        assert f_it.close(), 'Could not close iterator'
        self.assertFalse(f_it.nextFeature(fet), 'Fetched feature after iterator closed, expected nextFeature() to return False')
        self.assertFalse(fet.isValid(), 'Valid feature fetched from closed iterator, should be invalid')

        # Test rewinding closed iterator
        self.assertFalse(f_it.rewind(), 'Rewinding closed iterator successful, should not be allowed')

    def testGetFeaturesSubsetAttributes(self):
        """ Test that expected results are returned when using subsets of attributes """

        tests = {'pk': set([1, 2, 3, 4, 5]),
                 'cnt': set([-200, 300, 100, 200, 400]),
                 'name': set(['Pear', 'Orange', 'Apple', 'Honey', NULL]),
                 'name2': set(['NuLl', 'PEaR', 'oranGe', 'Apple', 'Honey'])}
        for field, expected in list(tests.items()):
            request = QgsFeatureRequest().setSubsetOfAttributes([field], self.provider.fields())
            result = set([f[field] for f in self.provider.getFeatures(request)])
            all_valid = (all(f.isValid() for f in self.provider.getFeatures(request)))
            self.assertEqual(result, expected, 'Expected {}, got {}'.format(expected, result))
            self.assertTrue(all_valid)

    def testGetFeaturesSubsetAttributes2(self):
        """ Test that other fields are NULL when fetching subsets of attributes """

        for field_to_fetch in ['pk', 'cnt', 'name', 'name2']:
            for f in self.provider.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([field_to_fetch], self.provider.fields())):
                # Check that all other fields are NULL and force name to lower-case
                for other_field in [field.name() for field in self.provider.fields() if field.name().lower() != field_to_fetch]:
                    if other_field == 'pk' or other_field == 'PK':
                        # skip checking the primary key field, as it may be validly fetched by providers to use as feature id
                        continue
                    self.assertEqual(f[other_field], NULL, 'Value for field "{}" was present when it should not have been fetched by request'.format(other_field))

    def testGetFeaturesNoGeometry(self):
        """ Test that no geometry is present when fetching features without geometry"""

        for f in self.provider.getFeatures(QgsFeatureRequest().setFlags(QgsFeatureRequest.NoGeometry)):
            self.assertFalse(f.hasGeometry(), 'Expected no geometry, got one')
            self.assertTrue(f.isValid())

    def testGetFeaturesWithGeometry(self):
        """ Test that geometry is present when fetching features without setting NoGeometry flag"""
        for f in self.provider.getFeatures(QgsFeatureRequest()):
            if f['pk'] == 3:
                # no geometry for this feature
                continue

            assert f.hasGeometry(), 'Expected geometry, got none'
            self.assertTrue(f.isValid())

    def testAddFeature(self):
        if not getattr(self, 'getEditableLayer', None):
            return

        l = self.getEditableLayer()
        self.assertTrue(l.isValid())

        f1 = QgsFeature()
        f1.setAttributes([6, -220, NULL, 'String', '15'])
        f1.setGeometry(QgsGeometry.fromWkt('Point (-72.345 71.987)'))

        f2 = QgsFeature()
        f2.setAttributes([7, 330, 'Coconut', 'CoCoNut', '13'])

        if l.dataProvider().capabilities() & QgsVectorDataProvider.AddFeatures:
            # expect success
            result, added = l.dataProvider().addFeatures([f1, f2])
            self.assertTrue(result, 'Provider reported AddFeatures capability, but returned False to addFeatures')
            f1.setId(added[0].id())
            f2.setId(added[1].id())

            # check result
            self.testGetFeatures(l.dataProvider(), [f1, f2])

            # add empty list, should return true for consistency
            self.assertTrue(l.dataProvider().addFeatures([]))

        else:
            # expect fail
            self.assertFalse(l.dataProvider().addFeatures([f1, f2]), 'Provider reported no AddFeatures capability, but returned true to addFeatures')

    def testDeleteFeatures(self):
        if not getattr(self, 'getEditableLayer', None):
            return

        l = self.getEditableLayer()
        self.assertTrue(l.isValid())

        #find 2 features to delete
        features = [f for f in l.dataProvider().getFeatures()]
        to_delete = [f.id() for f in features if f.attributes()[0] in [1, 3]]

        if l.dataProvider().capabilities() & QgsVectorDataProvider.DeleteFeatures:
            # expect success
            result = l.dataProvider().deleteFeatures(to_delete)
            self.assertTrue(result, 'Provider reported DeleteFeatures capability, but returned False to deleteFeatures')

            # check result
            self.testGetFeatures(l.dataProvider(), skip_features=[1, 3])

            # delete empty list, should return true for consistency
            self.assertTrue(l.dataProvider().deleteFeatures([]))

        else:
            # expect fail
            self.assertFalse(l.dataProvider().deleteFeatures(to_delete),
                             'Provider reported no DeleteFeatures capability, but returned true to deleteFeatures')

    def testTruncate(self):
        if not getattr(self, 'getEditableLayer', None):
            return

        l = self.getEditableLayer()
        self.assertTrue(l.isValid())

        features = [f['pk'] for f in l.dataProvider().getFeatures()]

        if l.dataProvider().capabilities() & QgsVectorDataProvider.FastTruncate or l.dataProvider().capabilities() & QgsVectorDataProvider.DeleteFeatures:
            # expect success
            result = l.dataProvider().truncate()
            self.assertTrue(result, 'Provider reported FastTruncate or DeleteFeatures capability, but returned False to truncate()')

            # check result
            features = [f['pk'] for f in l.dataProvider().getFeatures()]
            self.assertEqual(len(features), 0)
        else:
            # expect fail
            self.assertFalse(l.dataProvider().truncate(),
                             'Provider reported no FastTruncate or DeleteFeatures capability, but returned true to truncate()')

    def testChangeAttributes(self):
        if not getattr(self, 'getEditableLayer', None):
            return

        l = self.getEditableLayer()
        self.assertTrue(l.isValid())

        #find 2 features to change
        features = [f for f in l.dataProvider().getFeatures()]
        # need to keep order here
        to_change = [f for f in features if f.attributes()[0] == 1]
        to_change.extend([f for f in features if f.attributes()[0] == 3])
        # changes by feature id, for changeAttributeValues call
        changes = {to_change[0].id(): {1: 501, 3: 'new string'}, to_change[1].id(): {1: 502, 4: 'NEW'}}
        # changes by pk, for testing after retrieving changed features
        new_attr_map = {1: {1: 501, 3: 'new string'}, 3: {1: 502, 4: 'NEW'}}

        if l.dataProvider().capabilities() & QgsVectorDataProvider.ChangeAttributeValues:
            # expect success
            result = l.dataProvider().changeAttributeValues(changes)
            self.assertTrue(result, 'Provider reported ChangeAttributeValues capability, but returned False to changeAttributeValues')

            # check result
            self.testGetFeatures(l.dataProvider(), changed_attributes=new_attr_map)

            # change empty list, should return true for consistency
            self.assertTrue(l.dataProvider().changeAttributeValues({}))

        else:
            # expect fail
            self.assertFalse(l.dataProvider().changeAttributeValues(changes),
                             'Provider reported no ChangeAttributeValues capability, but returned true to changeAttributeValues')

    def testChangeGeometries(self):
        if not getattr(self, 'getEditableLayer', None):
            return

        l = self.getEditableLayer()
        self.assertTrue(l.isValid())

        # find 2 features to change
        features = [f for f in l.dataProvider().getFeatures()]
        to_change = [f for f in features if f.attributes()[0] == 1]
        to_change.extend([f for f in features if f.attributes()[0] == 3])
        # changes by feature id, for changeGeometryValues call
        changes = {to_change[0].id(): QgsGeometry.fromWkt('Point (10 20)'), to_change[1].id(): QgsGeometry()}
        # changes by pk, for testing after retrieving changed features
        new_geom_map = {1: QgsGeometry.fromWkt('Point ( 10 20 )'), 3: QgsGeometry()}

        if l.dataProvider().capabilities() & QgsVectorDataProvider.ChangeGeometries:
            # expect success
            result = l.dataProvider().changeGeometryValues(changes)
            self.assertTrue(result,
                            'Provider reported ChangeGeometries capability, but returned False to changeGeometryValues')

            # check result
            self.testGetFeatures(l.dataProvider(), changed_geometries=new_geom_map)

            # change empty list, should return true for consistency
            self.assertTrue(l.dataProvider().changeGeometryValues({}))

        else:
            # expect fail
            self.assertFalse(l.dataProvider().changeGeometryValues(changes),
                             'Provider reported no ChangeGeometries capability, but returned true to changeGeometryValues')

    def testChangeFeatures(self):
        if not getattr(self, 'getEditableLayer', None):
            return

        l = self.getEditableLayer()
        self.assertTrue(l.isValid())

        features = [f for f in l.dataProvider().getFeatures()]

        # find 2 features to change attributes for
        features = [f for f in l.dataProvider().getFeatures()]
        # need to keep order here
        to_change = [f for f in features if f.attributes()[0] == 1]
        to_change.extend([f for f in features if f.attributes()[0] == 2])
        # changes by feature id, for changeAttributeValues call
        attribute_changes = {to_change[0].id(): {1: 501, 3: 'new string'}, to_change[1].id(): {1: 502, 4: 'NEW'}}
        # changes by pk, for testing after retrieving changed features
        new_attr_map = {1: {1: 501, 3: 'new string'}, 2: {1: 502, 4: 'NEW'}}

        # find 2 features to change geometries for
        to_change = [f for f in features if f.attributes()[0] == 1]
        to_change.extend([f for f in features if f.attributes()[0] == 3])
        # changes by feature id, for changeGeometryValues call
        geometry_changes = {to_change[0].id(): QgsGeometry.fromWkt('Point (10 20)'), to_change[1].id(): QgsGeometry()}
        # changes by pk, for testing after retrieving changed features
        new_geom_map = {1: QgsGeometry.fromWkt('Point ( 10 20 )'), 3: QgsGeometry()}

        if l.dataProvider().capabilities() & QgsVectorDataProvider.ChangeGeometries and l.dataProvider().capabilities() & QgsVectorDataProvider.ChangeAttributeValues:
            # expect success
            result = l.dataProvider().changeFeatures(attribute_changes, geometry_changes)
            self.assertTrue(result,
                            'Provider reported ChangeGeometries and ChangeAttributeValues capability, but returned False to changeFeatures')

            # check result
            self.testGetFeatures(l.dataProvider(), changed_attributes=new_attr_map, changed_geometries=new_geom_map)

            # change empty list, should return true for consistency
            self.assertTrue(l.dataProvider().changeFeatures({}, {}))

        elif not l.dataProvider().capabilities() & QgsVectorDataProvider.ChangeGeometries:
            # expect fail
            self.assertFalse(l.dataProvider().changeFeatures(attribute_changes, geometry_changes),
                             'Provider reported no ChangeGeometries capability, but returned true to changeFeatures')
        elif not l.dataProvider().capabilities() & QgsVectorDataProvider.ChangeAttributeValues:
            # expect fail
            self.assertFalse(l.dataProvider().changeFeatures(attribute_changes, geometry_changes),
                             'Provider reported no ChangeAttributeValues capability, but returned true to changeFeatures')
