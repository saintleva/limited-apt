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

from lxml import etree


class Urls:

    def __init__(self):
        self.enclosure_debug_mode = False
        self.enclosure = ""
        self.debconf_priorities = ""

    def import_from_xml_element(self, base_element):
        self.enclosure_debug_mode = bool(base_element.get("enclosure-debug-mode"))
        self.enclosure = base_element.find("enclosure").get("url")
        self.debconf_priorities = base_element.find("debconf-priorities").get("url")


class SpaceAmount:

    def __init__(self, is_relative, number):
        self.is_relative = is_relative
        self.number = number

    def less_or_equal_to_other(self, remaining_space, all_space):
        return self.number * all_space <= remaining_space if self.is_relative else self.number <= remaining_space

    @staticmethod
    def from_string(string):
        if string.endswith("%"):
            return SpaceAmount(True, float(string[:-1]) / 100)
        elif string.endswith("B"):
            return SpaceAmount(False, int(string[:-1]))
        elif string.endswith("KB"):
            return SpaceAmount(False, 1000 * int(string[:-2]))
        elif string.endswith("KiB"):
            return SpaceAmount(False, 2 ** 10 * int(string[:-3]))
        elif string.endswith("MB"):
            return SpaceAmount(False, 1000_1000 * int(string[:-2]))
        elif string.endswith("MiB"):
            return SpaceAmount(False, 2 ** 20 * int(string[:-3]))
        elif string.endswith("MB"):
            return SpaceAmount(False, 1000_1000 * int(string[:-2]))
        elif string.endswith("MiB"):
            return SpaceAmount(False, 2 ** 20 * int(string[:-3]))
        elif string.endswith("GB"):
            return SpaceAmount(False, 1000_1000_1000 * int(string[:-2]))
        elif string.endswith("GiB"):
            return SpaceAmount(False, 2 ** 30 * int(string[:-3]))
        elif string.endswith("TB"):
            return SpaceAmount(False, 1000_1000_1000_1000 * int(string[:-2]))
        elif string.endswith("TiB"):
            return SpaceAmount(False, 2 ** 40 * int(string[:-3]))

class MinimalFreeSpace:

    def __init__(self):
        self.apt_archives = 0
        self.usr = 0


class Settings:

    def __init__(self):
        self.urls = Urls()
        self.minimal_free_space = MinimalFreeSpace()

    def import_from_xml(self, file):
        try:
            root = etree.parse(file).getroot()
            self.urls.import_from_xml_element(root.find("urls"))
            self.minimal_free_space.import_from_xml_element(root.find("minimal-free-space"))
        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
            raise UpdateTimesImportSyntaxError("Syntax error has been appeared during importing "
                                               "program settings from xml: " + str(err))