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
from .errors import DataError


class SettingsImportError(DataError): pass

class NoEnclosureSpecified(SettingsImportError): pass

class BadSpaceAmount(SettingsImportError): pass


class EnclosureRecord:

    def __init__(self, filename, url):
        self.filename = filename
        self.url = url


class Urls:

    def __init__(self):
        self.enclosure_debug_mode = False
        self.enclosures = []
        self.debconf_priorities = ""

    def export_to_xml_element(self, parent):
        base_element = etree.SubElement(parent, "urls", {"enclosure-debug-mode" : False})
        for enclosure in self.enclosures:
            etree.SubElement(base_element, "enclosure", filename=enclosure.filename, url=enclosure.url)
        etree.SubElement(base_element, "debconf-priorities", url=self.debconf_priorities)

    def import_from_xml_element(self, base_element):
        self.enclosure_debug_mode = bool(base_element.get("enclosure-debug-mode")) or False
        for enclosure_element in base_element.findall("enclosure"):
            self.enclosures.append(EnclosureRecord(enclosure_element.get("filename"), enclosure_element.get("url")))
        if not self.enclosure_debug_mode and not self.enclosures:
            raise NoEnclosureSpecified("No enclosure specified")
        self.debconf_priorities = base_element.find("debconf-priorities").get("url")


class SpaceAmount:

    def __init__(self, is_relative = None, number = None):
        self.is_relative = is_relative or False
        self.number = number or 0

    def less_or_equal_to_other(self, remaining_space, all_space):
        return self.number * all_space <= remaining_space if self.is_relative else self.number <= remaining_space

    def __str__(self):
        return "%.2f" % (number * 100) + "%" if self.is_relative else number + "B"

    @staticmethod
    def from_string(string):
        try:
            if string.endswith("%"):
                return SpaceAmount(True, float(string[:-1]) / 100)
            elif string.endswith("B"):
                return SpaceAmount(False, int(string[:-1]))
            elif string.endswith("KB"):
                return SpaceAmount(False, 1000 * int(string[:-2]))
            elif string.endswith("KiB"):
                return SpaceAmount(False, 2 ** 10 * int(string[:-3]))
            elif string.endswith("MB"):
                return SpaceAmount(False, 1000_000 * int(string[:-2]))
            elif string.endswith("MiB"):
                return SpaceAmount(False, 2 ** 20 * int(string[:-3]))
            elif string.endswith("GB"):
                return SpaceAmount(False, 1000_000_000 * int(string[:-2]))
            elif string.endswith("GiB"):
                return SpaceAmount(False, 2 ** 30 * int(string[:-3]))
            elif string.endswith("TB"):
                return SpaceAmount(False, 1000_000_000_000 * int(string[:-2]))
            elif string.endswith("TiB"):
                return SpaceAmount(False, 2 ** 40 * int(string[:-3]))
            else:
                raise BadSpaceAmount('String "{0}" cannot be a space amount'.format(string))
        except:
            raise BadSpaceAmount('String "{0}" cannot be a space amount'.format(string))

class MinimalFreeSpace:

    def __init__(self):
        self.apt_archives = SpaceAmount()
        self.usr = SpaceAmount()

    def export_to_xml_element(self, parent):
        base_element = etree.SubElement(parent, "minimal-free-space")
        etree.SubElement(base_element, "apt-archives", amount=str(self.apt_archives))
        etree.SubElement(base_element, "usr", amount=str(self.usr))

    def import_from_xml_element(self, base_element):
        self.apt_archives = SpaceAmount.from_string(base_element.find("apt-archives").get("amount"))
        self.usr = SpaceAmount.from_string(base_element.find("usr").get("amount"))


class Settings:

    def __init__(self):
        self.urls = Urls()
        self.minimal_free_space = MinimalFreeSpace()
        self.updatetime_module = None

    def export_to_xmo(self, file):
        root = etree.Element("settings")
        tree = etree.ElementTree(root)
        self.urls.export_to_xml_element(root)
        self.minimal_free_space.export_to_xml_element(root)
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)

    def import_from_xml(self, file):
        try:
            root = etree.parse(file).getroot()
            self.urls.import_from_xml_element(root.find("urls"))
            self.minimal_free_space.import_from_xml_element(root.find("minimal-free-space"))
        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
            raise SettingsImportError("Syntax error has been appeared during importing program settings from xml: " + str(err))