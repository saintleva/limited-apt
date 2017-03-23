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
from limitedapt.enclosure import *


class EnclosureTestCase(unittest.TestCase):

    def test_contains(self):
        _enclosure = Enclosure()
        _enclosure.import_from_xml("data/enclosure1")
        _enclosure.export_to_xml("data/enclosure1.copy")
        
#         self.assertNotIn(VersionedPackage("systemsettings", "amd64", "1.0"), _enclosure)
#         
#         self.assertIn(VersionedPackage("3dchess", "amd64", "0.0.1"), _enclosure)
#         self.assertIn(VersionedPackage("3dchess", "armel", "0.8.1-17"), _enclosure)
#         self.assertNotIn(VersionedPackage("3dchess", "armel", "0.0.2"), _enclosure)
#         
#         self.assertIn(VersionedPackage("libc6", "sparc", "0.0.1"), _enclosure)
#         self.assertIn(VersionedPackage("libxt6", "sparc", "0.0.1"), _enclosure)
#         self.assertIn(VersionedPackage("libxt6", "some", "0.0.2"), _enclosure)
#         
#         self.assertIn(VersionedPackage("libsdl-image1.2", "i386", "1.2.10-2+b2"), _enclosure)
#         self.assertIn(VersionedPackage("libsdl-image1.2", "i386", "1.2.12-2"), _enclosure)
#         self.assertIn(VersionedPackage("libsdl-image1.2", "i386", "0.0.1"), _enclosure)
#         self.assertIn(VersionedPackage("libsdl-image1.2", "amd64", "1.2.12-2"), _enclosure)
#         self.assertIn(VersionedPackage("libsdl-image1.2", "amd64", "1.2.12-5+b2"), _enclosure)

        self.assertNotIn(VersionedPackage("extremetuxracer", "some-arch", "0.0.1"), _enclosure)
        self.assertIn(VersionedPackage("extremetuxracer", "some-arch", "0.4-5"), _enclosure)

if __name__ == "__main__":
    unittest.main(verbosity=2)