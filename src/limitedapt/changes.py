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

#TODO: maybe remove it
from apt.cache import *
from limitedapt.tasks import *


class AllChanges:

    def __init__(self):
        self.logically_installed = set()
        self.physically_installed = set()
        self.logically_installed_but_physically_upgraded = set()
        self.upgraded = set()
        self.reinstalled = set()
        self.downgraded = set()
        self.logically_removed = set()
        self.physically_removed = set()
        self.kept = set()


def get_all_changes(changes, tasks):
    result = AllChanges()
    for pkg in changes:
        if pkg.marked_install:
            if pkg.is_installed:
                if pkg in tasks.installed:
                    if not pkg.marked_upgrade:
                        result.logically_installed.add(pkg)

    for pkg in tasks.install:
        if not pkg.
