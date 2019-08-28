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

from datetime import datetime
import os.path
from lxml import etree
from limitedapt.errors import XmlImportSyntaxError


class UpdateTimesImportSyntaxError(XmlImportSyntaxError): pass


class UpdateTimes:

    STR_FORMAT = "%Y-%m-%d %H:%M:%S"

    @property
    def distro(self):
        try:
            file_time = os.path.getmtime("/var/cache/apt/pkgcache.bin")
        except:
            file_time = 0
        return max(self.__distro, file_time)

    @distro.setter
    def distro(self, distro):
        self.__distro = distro

    @property
    def enclosure(self):
        return self.__enclosure

    @enclosure.setter
    def enclosure(self, enclosure):
        self.__enclosure = enclosure

    def export_to_xml(self, file):
        root = etree.Element("updatetime")
        etree.SubElement(root, "distro", time=self.distro.strftime(STR_FORMAT))
        etree.SubElement(root, "enclosure", time=self.enclosure.strftime(STR_FORMAT))
        tree = etree.ElementTree(root)
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)

    def import_from_xml(self, file):
        try:
            root = etree.parse(file).getroot()
            distro_element = root.find("distro")
            self.distro = datetime.strptime(distro_element.get("time"), STR_FORMAT)
            enclosure_element = root.find("enclosure")
            self.enclosure = datetime.strptime(enclosure_element.get("time"), STR_FORMAT)
        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
            raise UpdateTimesImportSyntaxError("Syntax error has been appeared during importing"
                                               "last time of updating from xml: " + str(err))