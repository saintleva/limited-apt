#
# Copyright (C) Anton Liaukevich 2011-2019 <leva.dev@gmail.com>
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

import itertools
import os
import time
import subprocess
import apt

from limitedapt.packages import VersionedPackage
from limitedapt.enclosure import *
from limitedapt.single import get_cache


def debug_suidbit(place):
    print(place, ":")
    print('UID = {0}, EUID = {1}'.format(os.getuid(), os.geteuid()))
    print()

    time_path = os.path.join('/sbin/test', str(time.time()))
    os.makedirs(time_path)
    print()

def update_enclosure_by_debtags(filename):
    enclosure = Enclosure()
    
    query = 'role::documentation || role::app-data || role::data || role::debug-symbols || ' + \
        '(role::source && ! use::driver) || role::metapackage || role::examples || ' + \
        'role::program && ( ! (security::antivirus || security::firewall) ) || ' + \
        '! ( (admin::configuring && admin::filesystem && admin::logging) || ' + \
        '(admin::logging && interface::daemon) || ' + \
        '(admin::kernel && interface::daemon) || admin::TODO)'

    found = subprocess.getoutput('debtags search "{0}"'.format(query))   
    lines = found.splitlines()
    seriated_names = [line.partition(" ")[0] for line in lines]
    names = list(key for key, _ in itertools.groupby(seriated_names))
    
    enclosure = Enclosure()
    enclosure.import_from_xml(filename)
    cache = get_cache()
    for name in names:
        pkg = cache[name]
        enclosure.add_versioned_package(VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version))

    enclosure.export_to_xml(filename)
