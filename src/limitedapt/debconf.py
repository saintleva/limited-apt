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
from limitedapt.errors import *


class DebconfError(Error): pass

class PackageAlreadyAdded(DebconfError): pass


def invert_dict(map):
    return { value, key for key, value in map }


PRIORITY_STR_MAP = {
    0 : "low",
    1 : "medium",
    2 : "high",
    3 : "critical"
}

PRIORITY_REVERSE_STR_MAP = invert_dict(PRIORITY_STR_MAP)

class Priority(enum.Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


STATUS_STR_MAP = {
    0 : "has-questions",
    1 : "has-not-questions",
    2 : "no-config-file",
    3 : "not-processed",
}

STATUS_REVERSE_STR_MAP = invert_dict(STATUS_STR_MAP)

class Status(enum.Enum):

    HAS_QUESTIONS = 0
    HAS_NOT_QUESTIONS = 1
    NO_CONFIG_FILE = 2
    HAVED_NOT_BEEN_PROCESSED = 3

    def __str__(self):
        return STATUS_STR_MAP[self.value]

def status_from_string(string):
    return Status(STATUS_REVERSE_STR_MAP[string])


class PackageState:

    def __init__(self, priority, status):
        self.priority = priority
        self.status = status


class DebconfPriorities:

    def __init__(self):
        self.__data = {}

    def add_package(self, package, state):
        if package.name in self.__data:
            arch_map = self.__data[package.name]
            if package.architecture in arch_map:
                raise PackageAlreadyAdded()
            arch_map[package.architecture] = state
        else:
            self.__data[package.name] = { package.architecture : state }

    def export_to_xml(self, file):
        root = etree.Element("packages")
        for package, archs in sorted(self.__data.items(), key=lambda x: x[0]):
            package_element = etree.SubElement(root, "package", name=package.name)
            for arch, state in sorted(archs):
                priority_str
                etree.SubElement(package_element, "arch", name=arch, status=state.status, )
        tree = etree.ElementTree(root)
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)
