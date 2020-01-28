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

import enum
from lxml import etree
from limitedapt.errors import Error


class DebconfError(Error): pass

class PackageAlreadyAdded(DebconfError): pass

class PackageNotInStructure(DebconfError): pass

class DebconfPrioritiesImportSyntaxError(DebconfError): pass


def invert_dict(map):
    return {value: key for key, value in map.items()}


PRIORITY_STR_MAP = {
    0: "low",
    1: "medium",
    2: "high",
    3: "critical"
}

REVERSE_PRIORITY_STR_MAP = invert_dict(PRIORITY_STR_MAP)

class Priority(enum.Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

    def __str__(self):
        #TODO: debug and remove it
        if self is None:
            return "NONE"

        return PRIORITY_STR_MAP[self.value]

    @staticmethod
    def from_string(string):
        return Priority(REVERSE_PRIORITY_STR_MAP[string])


STATUS_STR_MAP = {
    0: "has-questions",
    1: "has-not-questions",
    2: "no-config-file",
    3: "not-processed",
    4: "processing-error"
}

REVERSE_STATUS_STR_MAP = invert_dict(STATUS_STR_MAP)

class Status(enum.Enum):
    HAS_QUESTIONS = 0
    HAS_NOT_QUESTIONS = 1
    NO_CONFIG_FILE = 2
    HAVE_NOT_BEEN_PROCESSED = 3
    PROCESSING_ERROR = 4

    def __str__(self):
        return STATUS_STR_MAP[self.value]

    @staticmethod
    def from_string(string):
        return Status(REVERSE_STATUS_STR_MAP[string])


class PackageState:

    def __init__(self, status, priority):
        self.status = status
        self.priority = priority

    def __eq__(self, other):
        if self.status == other.status:
            if self.status == Status.HAS_QUESTIONS:
                return self.priority == other.priority
            else:
                return True


class DebconfPriorities:

    def __init__(self):
        self.__data = {}

    def clear(self):
        self.__data.clear()

    def add_package(self, package, state):
        if package.name in self.__data:
            arch_map = self.__data[package.name]
            if package.architecture in arch_map:
                raise PackageAlreadyAdded()
            arch_map[package.architecture] = state
        else:
            self.__data[package.name] = {package.architecture: state}

    def get_state(self, package):
        try:
            print(package)
            self.__data[package.name][package.architecture]
        except KeyError:
            raise PackageNotInStructure()

    def export_to_xml(self, file):
        root = etree.Element("debconf-priorities")
        for package, archs in sorted(self.__data.items(), key=lambda x: x[0]):
            package_element = etree.SubElement(root, "package", name=package)
            for arch, state in sorted(archs.items(), key=lambda x: x[0]):
                priority_str = str(state.priority) if state.status == Status.HAS_QUESTIONS else ""
                if state.status == Status.HAS_QUESTIONS:

                    #TODO: debug and remove it
                    print(state.priority)

                    etree.SubElement(package_element, "arch", name=arch, status=str(state.status),
                                     priority=str(state.priority))
                else:
                    etree.SubElement(package_element, "arch", name=arch, status=str(state.status))
        tree = etree.ElementTree(root)
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)

    def import_from_xml(self, file):
#        try:
        root = etree.parse(file).getroot()
        self.clear()
        for package_element in root.findall("package"):
            package_name = package_element.get("name")
            if package_name not in self.__data:
                self.__data[package_name] = {}
            arch_map = self.__data[package_name]
            for arch_element in package_element.findall("arch"):
                status = Status.from_string(arch_element.get("status"))
                if status == Status.HAS_QUESTIONS:
                    priority = Priority.from_string(arch_element.get("priority"))
                else:
                    priority = None
                arch_map[arch_element.get("arch")] = PackageState(status, priority)
#        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
#            raise DebconfPrioritiesImportSyntaxError(
#               '''Syntax error has been appeared during deconf priority table from xml: ''' + str(err))