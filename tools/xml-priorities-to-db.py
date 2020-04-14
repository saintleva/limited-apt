#!/usr/bin/env python3
#
# Copyright (C) Anton Liaukevich 2011-2020 <leva.dev@gmail.com>
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

import sys
import time
from limitedapt.debconf import *


def main():
    map_priorities = DebconfPriorities()
    before_xml_import_time = time.time()
    map_priorities.import_from_xml(sys.argv[1])
    after_xml_import_time = time.time()
    print("{0} seconds elapsed for xml importing".format(after_xml_import_time - before_xml_import_time))
    before_db_create_time = time.time()
    debconf_priorities_map_to_db(map_priorities, "sqlite:///" + sys.argv[2])
    after_db_create_time = time.time()
    print("{0} seconds elapsed for db creating".format(after_db_create_time - before_db_create_time))


if __name__ == "__main__":
    main()