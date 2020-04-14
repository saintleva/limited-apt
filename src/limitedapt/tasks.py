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

from lxml import etree
import apt.package
from .packages import *
from .single import get_cache


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
                    self.__container.append(ConcretePackage(pkg.shortname, pkg.candidate.architecture))

    def __bool__(self):
        return bool(self.__container)

    def __contains__(self, package):
        if isinstance(package, apt.package.Package):
            cache = get_cache()
            return ConcretePackage(package.shortname, package.candidate.architecture) in self.__container
        elif isinstance(package, ConcretePackage):
            return package in self.__container
        else:
            raise TypeError("ConcretePackage or apt.package.Package instance is required")

    def __iter__(self):
        return iter(self.__container)

    def pkgs(self):
        cache = get_cache()
        for package in self.__container:
            yield cache[str(package)]

    def __add__(self, other):
        result = OnetypeRealTasks()
        result.__container = self.__container + other.__container
        return result

    def remove(self, concrete_package):
        self.__container.remove(concrete_package)

    def clear(self):
        self.__container.clear()

    def append(self, package):
        self.__container.append(package)


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

    def export_to_xml_element(self, parent):

        def export_onetype(type, container):
            onetype_element = etree.SubElement(parent, type)
            for package in container:
                etree.SubElement(onetype_element, "package", name=package.name, arch=package.architecture)

        export_onetype("install", self.install)
        export_onetype("remove", self.remove)
        export_onetype("physically-remove", self.physically_remove)
        export_onetype("purge", self.purge)
        export_onetype("markauto", self.markauto)
        export_onetype("unmarkauto", self.unmarkauto)

    def import_from_xml_element(self, parent):

        def import_onetype(type, container):
            onetype_element = parent.find(type)
            container.clear()
            for package_element in onetype_element.findall("package"):
                container.append(ConcretePackage(package_element.get("name"), package_element.get("arch")))

        import_onetype("install", self.__install)
        import_onetype("remove", self.__remove)
        import_onetype("physically-remove", self.__physically_remove)
        import_onetype("purge", self.__purge)
        import_onetype("markauto", self.__markauto)
        import_onetype("unmarkauto", self.__unmarkauto)
