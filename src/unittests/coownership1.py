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
from limitedapt.coownership import *


class CoownershipTestCase1(unittest.TestCase):

    def setUp(self):
        self._coownership = CoownershipList()
        self._coownership.import_from_xml("data/coownership1")

    def test_is_own(self):
        self.assertTrue(self._coownership.is_own(ConcretePackage("extremetuxracer", "amd64"), "anthony"))
        self.assertTrue(self._coownership.is_own(ConcretePackage("extremetuxracer", "amd64"), "galina"))
        self.assertFalse(self._coownership.is_own(ConcretePackage("3dchess", "amd64"), "not-a-user"))
        self.assertFalse(self._coownership.is_own(ConcretePackage("not-a-package", "not-an-arch"), "olduser1"))

    def test_sets(self):
        owners1 = self._coownership.owners_of(ConcretePackage("extremetuxracer", "amd64"))
        self.assertSetEqual(owners1, {"1", "2", "4", "a", "anthony", "g", "galina", "henady", "hey"})
        owners2 = self._coownership.owners_of(ConcretePackage("extremetuxracer", "i386"))
        self.assertSetEqual(owners2, {"olduser1", "olduser2"})
    
    def test_no_owner(self):
        owners = self._coownership.owners_of(ConcretePackage("nobody-own-me", "amd64"))
        self.assertSetEqual(owners, set())

    def test_his_packages(self):
        self.assertSetEqual(set(self._coownership.his_packages("not-a-user")), set())
        self.assertSetEqual(set(self._coownership.his_packages("root")),
                            { ConcretePackage("3dchess", "amd64") })
        self.assertSetEqual(set(self._coownership.his_packages("anthony")),
                            { ConcretePackage("extremetuxracer", "amd64"),
                              ConcretePackage("python3-doc", "all"),
                              ConcretePackage("konsole", "armhf") })
        

class CoownershipFileTestCase(unittest.TestCase):
 
    def test_file_dont_exist(self):
        self._coownership = CoownershipList()
        with self.assertRaises(OSError):
            self._coownership.import_from_xml("data/not-a-file")        
            
    def test_file_invalid_syntax(self):
        self._coownership = CoownershipList()
        with self.assertRaises(CoownershipImportSyntaxError):
            self._coownership.import_from_xml("data/abrakadabra")        
            

class CoownershipEditTestCase(unittest.TestCase):            

    def setUp(self):
        self._coownership = CoownershipList()
        self._coownership.import_from_xml("data/coownership1")

    def test_add(self):
        with self.assertRaises(UserAlreadyOwnsThisPackage):
            self._coownership.add_ownership(ConcretePackage("python3-doc", "all"), "anthony")
        self._coownership.add_ownership(ConcretePackage("xterm", "i386"), "galina")
        self.assertSetEqual(set(self._coownership.his_packages("galina")),
                            { ConcretePackage("extremetuxracer", "amd64"),
                              ConcretePackage("xterm", "i386") })        
        self._coownership.add_ownership(ConcretePackage("kate", "i386"), "anthony", True)        
        self.assertTrue(self._coownership.is_own(ConcretePackage("kate", "i386"), "root"))
        
    def test_remove_ownership(self):
        with self.assertRaises(PackageIsNotInstalled):
            self._coownership.remove_ownership(ConcretePackage("not-a-package", "not-an-arch"), "anthony")
        with self.assertRaises(UserDoesNotOwnPackage):
            self._coownership.remove_ownership(ConcretePackage("3dchess", "amd64"), "anthony")
        self._coownership.remove_ownership(ConcretePackage("3dchess", "amd64"), "root2")
        
        self.assertFalse(self._coownership.is_own(ConcretePackage("3dchess", "amd64"), "root2"))
        
    def test_remove_package(self):
        with self.assertRaises(PackageIsNotInstalled):
            self._coownership.remove_ownership(ConcretePackage("not-a-package", "not-an-arch"), "anthony")
        self._coownership.remove_package(ConcretePackage("extremetuxracer", "amd64"))
        owners = self._coownership.owners_of(ConcretePackage("extremetuxracer", "amd64"))
        self.assertSetEqual(owners, set())
        
if __name__ == "__main__":
    unittest.main(verbosity=2)