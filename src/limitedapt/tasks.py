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


class Tasks:

    def __init__(self):
        self.install = []
        self.remove = []
        self.physically_remove = []
        self.purge = []
        self.markauto = []
        self.unmarkauto = []


class OnetypeConcretePkgTasks:

    def __init__(self, cache, onetype_tasks):
        self.__container = set()
        for task in onetype_tasks:
            pkg = cache[task]
            self.__container.add(ConcretePackage(pkg.name, pkg.candidate.architecture))

    def __contains__(self, pkg):
        #TODO: debug and remove it:
        #print("YO!")
        return ConcretePackage(pkg.name, pkg.candidate.architecture) in self.__container


class ConcretePkgTasks:

    def __init__(self, cache, tasks):
        self.__install = OnetypeConcretePkgTasks(cache, tasks.install)
        self.__remove = OnetypeConcretePkgTasks(cache, tasks.remove)
        self.__physically_remove = OnetypeConcretePkgTasks(cache, tasks.physically_remove)
        self.__purge = OnetypeConcretePkgTasks(cache, tasks.purge)
        self.__markauto = OnetypeConcretePkgTasks(cache, tasks.markauto)
        self.__unmarkauto = OnetypeConcretePkgTasks(cache, tasks.unmarkauto)

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
