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

import apt.package
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

    def __init__(self, onetype_tasks = None):
        self.__container = []
        if onetype_tasks is not None:
            cache = get_cache()
            for task in onetype_tasks:
                if task in cache: # Emit packages that are not in repository
                    pkg = cache[task]
                    self.__container.append(pkg)

    def __bool__(self):
        return bool(self.__container)

    def __contains__(self, package):
        if isinstance(package, apt.package.Package):
            return package in self.__container
        elif isinstance(package, ConcretePackage):
            cache = get_cache()
            return cache[str(package)] in self.__container
        else:
            raise TypeError("ConcretePackage or apt.package.Package instance is required")

    def __iter__(self):
        return iter(self.__container)

    def __add__(self, other):
        result = OnetypeRealTasks()
        result.__container = self.__container + other.__container
        return result

    def remove(self, concrete_package):
        cache = get_cache()
        pkg = cache[str(concrete_package)]
        self.__container.remove(pkg)

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

    def is_empty(self):
        return not (self.install or self.remove or self.physically_remove or self.purge or self.markauto or self.unmarkauto)
