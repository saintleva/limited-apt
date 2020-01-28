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
from limitedapt.settings import *


class UpdateTimeTestCase1(unittest.TestCase):

    def setUp(self):
        self.__settings = Settings("/usr/local/etc/limited-apt/")
        self.__settings.import_from_xml("data/settings1")

    def test_1(self):
        self.assertEqual(self.__settings.urls.enclosure_debug_mode, True)
        self.assertIn(EnclosureRecord("1", "https://www.github.com/saintleva/limited-apt/data/enclosure1"),
                      self.__settings.urls.enclosures)
        self.assertIn(EnclosureRecord("2", "https://www.github.com/saintleva/limited-apt/data/enclosure2"),
                      self.__settings.urls.enclosures)


if __name__ == "__main__":
    unittest.main(verbosity=2)