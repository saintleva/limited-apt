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
from datetime import *
from limitedapt.updatetime import *

class UpdateTimeTestCase1(unittest.TestCase):

    def setUp(self):
        self.__update_times = UpdateTimes()
        self.__update_times.distro = datetime.now()

    def test_not_now(self):
        self.assertNotEquals(self.__update_times.distro, datetime.now())


if __name__ == "__main__":
    unittest.main(verbosity=2)