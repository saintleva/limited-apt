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


import os
import unittest
import difflib
from limitedapt.coownership import *
from limitedapt.enclosure import *


def create_machine_copy():
    if not os.path.exists("data/coownership1"):
        coownership = CoownershipList()
        coownership.import_from_xml("data/coownership1-orig")
        coownership.export_to_xml("data/coownership1")
    if not os.path.exists("data/enclosure1"):
        enclosure = Enclosure()
        enclosure.import_from_xml("data/enclosure1-orig")
        enclosure.export_to_xml("data/enclosure1")        


class FilesDiffTestCase(unittest.TestCase):
    
    def test_coownership_file(self):
        coownership = CoownershipList()
        coownership.import_from_xml("data/coownership1")
        coownership.export_to_xml("data/coownership1.copy")
        
        with open("data/coownership1") as importedtFile:
            importedLines = importedtFile.readlines()
        with open("data/coownership1.copy") as exportedtFile:
            exportedLines = exportedtFile.readlines()
        
        diff = difflib.unified_diff(importedLines, exportedLines)
        
        changes = len(list(diff))
        self.assertEqual(changes, 0)
       
    def test_enclosure_file(self):
        enclosure = Enclosure()
        enclosure.import_from_xml("data/enclosure1")
        enclosure.export_to_xml("data/enclosure1.copy")
        
        with open("data/enclosure1") as importedtFile:
            importedLines = importedtFile.readlines()
        with open("data/enclosure1.copy") as exportedtFile:
            exportedLines = exportedtFile.readlines()
        
        diff = difflib.unified_diff(importedLines, exportedLines)
        
        changes = len(list(diff))
        self.assertEqual(changes, 0)
        
       
if __name__ == "__main__":
    create_machine_copy()
    unittest.main(verbosity=2)    
