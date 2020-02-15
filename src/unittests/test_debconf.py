#!/usr/bin/env python3
#
# Copyright (C) Anton Liaukevich 2011-2017 <leva.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import unittest
from limitedapt.packages import *
from limitedapt.debconf import *


class DebconfTestCase1(unittest.TestCase):

    def setUp(self):
        self.__debconf = DebconfPriorities()
        self.__debconf.import_from_xml("data/debconf-priorities1")

    def test_bad_import(self):
        debconf = DebconfPriorities()
        with self.assertRaises(DebconfPrioritiesImportSyntaxError):
            debconf.import_from_xml("data/abrakadabra")

    def test_contains(self):
        self.assertIn(ConcretePackage("adonthell-data", "all"), self.__debconf)
        self.assertNotIn(ConcretePackage("adonthell-data", "not-architecture"), self.__debconf)
        self.assertNotIn(ConcretePackage("python3-apt", "i386"), self.__debconf)

    def test_equal(self):
        self.assertEqual(self.__debconf[ConcretePackage("3dchess", "i386")],
                         PackageState(Status.HAS_QUESTIONS, Priority.LOW))
        self.assertNotEqual(self.__debconf[ConcretePackage("3dchess", "amd64")],
                         PackageState(Status.HAS_QUESTIONS, Priority.LOW))
        self.assertEqual(self.__debconf[ConcretePackage("3dchess", "armel")],
                         PackageState(Status.HAS_QUESTIONS, Priority.HIGH))
        self.assertEqual(self.__debconf[ConcretePackage("abe", "amd64")],
                         PackageState(Status.HAS_QUESTIONS, Priority.CRITICAL))
        self.assertEqual(self.__debconf[ConcretePackage("abe", "armel")],
                         PackageState(Status.HAS_NOT_QUESTIONS))
        self.assertEqual(self.__debconf[ConcretePackage("ace-of-penguins", "amd64")],
                         PackageState(Status.PROCESSING_ERROR))
        self.assertEqual(self.__debconf[ConcretePackage("ace-of-penguins", "i386")],
                         PackageState(Status.NO_CONFIG_FILE))

    def test_exceptions(self):
        with self.assertRaises(KeyError):
            self.__debconf[ConcretePackage("python3-apt", "i386")]

if __name__ == "__main__":
    unittest.main(verbosity=2)