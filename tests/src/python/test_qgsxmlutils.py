# -*- coding: utf-8 -*-
"""QGIS Unit tests for QgsXmlUtils.

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
__author__ = 'Matthias Kuhn'
__date__ = '18/11/2016'
__copyright__ = 'Copyright 2016, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import qgis  # NOQA switch sip api

from qgis.core import QgsXmlUtils

from qgis.PyQt.QtXml import QDomDocument

from qgis.testing import start_app, unittest


start_app()


class TestQgsXmlUtils(unittest.TestCase):

    def test_integer(self):
        """
        Test that maps are correctly loaded and written
        """
        doc = QDomDocument("properties")

        my_properties = {'a': 1, 'b': 2, 'c': 3, 'd': -1}
        elem = QgsXmlUtils.writeVariant(my_properties, doc)

        prop2 = QgsXmlUtils.readVariant(elem)
        self.assertEqual(my_properties, prop2)

    def test_string(self):
        """
        Test that maps are correctly loaded and written
        """
        doc = QDomDocument("properties")

        my_properties = {'a': 'a', 'b': 'b', 'c': 'something_else', 'empty': ''}
        elem = QgsXmlUtils.writeVariant(my_properties, doc)

        prop2 = QgsXmlUtils.readVariant(elem)

        self.assertEqual(my_properties, prop2)

    def test_double(self):
        """
        Test that maps are correctly loaded and written
        """
        doc = QDomDocument("properties")

        my_properties = {'a': 0.27, 'b': 1.0, 'c': 5}
        elem = QgsXmlUtils.writeVariant(my_properties, doc)

        prop2 = QgsXmlUtils.readVariant(elem)

        self.assertEqual(my_properties, prop2)

    def test_boolean(self):
        """
        Test that maps are correctly loaded and written
        """
        doc = QDomDocument("properties")

        my_properties = {'a': True, 'b': False}
        elem = QgsXmlUtils.writeVariant(my_properties, doc)

        prop2 = QgsXmlUtils.readVariant(elem)

        self.assertEqual(my_properties, prop2)

    def test_list(self):
        """
        Test that lists are correctly loaded and written
        """
        doc = QDomDocument("properties")
        my_properties = [1, 4, 'a', 'test', 7.9]
        elem = QgsXmlUtils.writeVariant(my_properties, doc)

        prop2 = QgsXmlUtils.readVariant(elem)

        self.assertEqual(my_properties, prop2)

    def test_complex(self):
        """
        Test that maps are correctly loaded and written
        """
        doc = QDomDocument("properties")

        my_properties = {'boolean': True, 'integer': False, 'map': {'a': 1}}
        elem = QgsXmlUtils.writeVariant(my_properties, doc)

        prop2 = QgsXmlUtils.readVariant(elem)

        self.assertEqual(my_properties, prop2)


if __name__ == '__main__':
    unittest.main()
