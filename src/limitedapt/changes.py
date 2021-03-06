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


class AllChanges:

    def __init__(self):
        self.logically_installed = []
        self.physically_installed = []
        self.logically_installed_but_physically_upgraded = []
        self.upgraded = []
        self.reinstalled = []
        self.downgraded = []
        self.logically_removed = []
        self.physically_removed = []
        self.purged = []
        self.kept = []


def get_all_changes(changes, tasks):
    result = AllChanges()

    for pkg in changes:
        if pkg.marked_install:
            result.physically_installed.append(pkg)
        else:
            if pkg.is_installed:
                if pkg in tasks.install:
                    if pkg.marked_upgrade and not pkg.marked_install:
                        result.logically_installed_but_physically_upgraded.append(pkg)
                elif pkg.marked_upgrade:
                    result.upgraded.append(pkg)
        if pkg.marked_reinstall:
            result.reinstalled.append(pkg)
        if pkg.marked_downgrade:
            result.downgraded.append(pkg)
        if pkg.marked_delete and pkg not in tasks.purge:
            result.physically_removed.append(pkg)
        if pkg.marked_keep:
            result.kept.append(pkg)

    for pkg in (tasks.install + tasks.unmarkauto).pkgs():
        if pkg.is_installed and not pkg.marked_upgrade:
            result.logically_installed.append(pkg)
    for pkg in (tasks.remove + tasks.markauto).pkgs():
        if not pkg.marked_delete:
            result.logically_removed.append(pkg)
    for pkg in tasks.purge.pkgs():
        result.purged.append(pkg)

    return result
