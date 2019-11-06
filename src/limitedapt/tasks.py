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

from limitedapt.packages import *
from limitedapt.single import get_cache


class Tasks:

    def __init__(self):
        self.install = []
        self.remove = []
        self.physically_remove = []
        self.purge = []
        self.markauto = []
        self.unmarkauto = []


class OnetypeRealTasks:

    def __init__(self):
        self.__container = set()

    def __init__(self, onetype_tasks):
        cache = get_cache()
        self.__container = set()
        for task in onetype_tasks:
            pkg = cache[task]
            self.__container.add(pkg)

    def __contains__(self, pkg):
        return pkg in self.__container

    def __iter__(self):
        return iter(self.__container)

    def __add__(self, other):
        result = OnetypeConcretePkgTasks()
        result.__container = self.__container + other.__container
        return result

    #TODO: remove it
    def __str__(self):

        def list_to_str(items):
            result = ""
            is_first = True
            for item in items:
                if not is_first:
                    result += ", "
                result += str(item)
                is_first = False
            return result

        for package in self.__container:
            return str(package) + ", "


class RealTasks:

    def __init__(self, tasks):
        self.__install = OnetypeRealTasks(tasks.install)
        self.__remove = OnetypeRealTasks(tasks.remove)
        self.__physically_remove = OnetypeRealTasks(tasks.physically_remove)
        self.__purge = OnetypeRealTasks(tasks.purge)
        self.__markauto = OnetypeRealTasks(tasks.markauto)
        self.__unmarkauto = OnetypeRealTasks(tasks.unmarkauto)

    @property
    def install(self):
        return self.__install

    @property
    def remove(self):
        return self.__remove

    @property
    def physically_remove(self):
        return self.__physically_remove

    @property
    def purge(self):
        return self.__purge

    @property
    def markauto(self):
        return self.__markauto

    @property
    def unmarkauto(self):
        return self.__unmarkauto
